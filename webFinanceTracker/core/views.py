from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import escape
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import Transaction
from .charts.prediction_plot import generate_prediction_plot
import datetime
import json
from importlib import import_module
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io
import datetime
import csv

class customLoginView(LoginView):
    template_name = 'core/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'core/base_unautheticated.html'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user

        if user.username == 'demo':
            last_reset = cache.get('demo_last_reset')
            now = datetime.datetime.now(datetime.timezone.utc)

            if not last_reset or (now - last_reset) > datetime.timedelta(hours=1):
                lock_key = 'demo_reset_lock'

                if cache.add(lock_key, 'locked', timeout=30):
                    try:
                        self._reset_demo_account(user)
                        cache.set('demo_last_reset', now)
                    finally:
                        cache.delete(lock_key)
                
                else:
                    import time
                    time.sleep(0.5)
                    if not cache.get(lock_key):
                        self._reset_demo_account(user)
                        cache.set('demo_last_reset', now)

        return response
    
    def _reset_demo_account(self, user):
        Transaction.objects.filter(user=user).delete()

        csv_path = settings.BASE_DIR / 'core' / 'demo_data.csv'
        if not csv_path.exists():
            print("Warning: demo_data.csv not found. Skipping import.")
            return
        
        try:
            with open(csv_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                expected_headers = ['Date', 'Category', 'Description', 'Amount', 'Type']
                if not all(header in reader.fieldnames for header in expected_headers):
                    print("Warning: Invalid CSV headers in demo_data.csv. Skipping import.")
                    return
                
                transactions = []
                for row in reader:
                    try:
                        dateStr = row['Date'].strip()
                        date = datetime.datetime.strptime(dateStr, '%Y-%m-%d').date()
                        category = row['Category'].strip()
                        description = row['Description'].strip()
                        amount = row['Amount'].strip()
                        type_ = row['Type'].strip()

                        if not all([category, description, amount, type_]):
                            continue

                        if not amount.replace('.', '').replace('-','').isdigit():
                            continue

                        if type_ not in ['expense', 'income']:
                            continue

                        transactions.append({
                            'date': date,
                            'category': category,
                            'description': description,
                            'amount': amount,
                            'type': type_
                        })
                    except ValueError:
                        continue

                transactions.sort(key=lambda x: x['date'])
                for transaction in transactions:
                    Transaction.objects.create(
                        user=user,
                        date=transaction['date'],
                        category=transaction['category'],
                        description=transaction['description'],
                        amount=transaction['amount'],
                        type=transaction['type']
                    )

            print(f"Demo account reset for user {user.username}")
        except Exception as e:
            print(f"Error resetting demo account: {e}")
    
class RegisterView(CreateView):
    template_name = 'core/register.html'
    form_class = UserCreationForm
    success_url = '/'

    def form_valid(self, form):
        self._cleanup_expired_users()

        if self._get_active_test_user_count() >= 3:
            messages.error(self.request, 'Maximum number of test accounts reached. Please try again later. Accounts expire after an hour.')
            return self.form_invalid(form)

        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Registration successful!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'core/base_unauthenticated.html'
        self._cleanup_expired_users()
        context['available_slots'] = 3 - self._get_active_test_user_count()
        return context
    
    def _cleanup_expired_users(self):
        expiry_time = timezone.now() - datetime.timedelta(hours=1)
        protected_usernames = ['admin', 'demo']
        expired_users = User.objects.filter(date_joined__lt=expiry_time).exclude(username__in=protected_usernames)
        expired_users.delete()

    def _get_active_test_user_count(self):
        protected_usernames = ['admin', 'demo']
        return User.objects.exclude(username__in=protected_usernames).count()
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Finance Tracker.')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})

@login_required
def analytics(request):
    expense_count = Transaction.objects.filter(user=request.user, type='expense').count()
    income_count = Transaction.objects.filter(user=request.user, type='income').count()
    transactions_count = Transaction.objects.filter(user=request.user).count()
    return JsonResponse({
        'expense_count': expense_count,
        'income_count': income_count,
        'transactions_count': transactions_count
    })

@login_required
def generate_feed_messages(request):
    now = datetime.datetime.now()
    currentMonth = now.month
    currentYear = now.year
    lastMonth = currentMonth - 1 if currentMonth > 1 else 12
    lastYear = currentYear if currentMonth > 1 else currentYear - 1

    allTransactions = Transaction.objects.filter(user=request.user, type='expense')

    currentMonthTransactions = [t for t in allTransactions if t.date.month == currentMonth and t.date.year == currentYear]
    lastMonthTransactions = [t for t in allTransactions if t.date.month == lastMonth and t.date.year == lastYear]

    def combine(transactions):
        description_totals = {}
        for t in transactions:
            description = t.description
            amount = t.get_amount()
            description_totals[description] = description_totals.get(description, float('0')) + abs(amount)
        return description_totals
    
    currentMonthTotals = combine(currentMonthTransactions)
    lastMonthTotals = combine(lastMonthTransactions)

    feed = []
    for description in set(currentMonthTotals) | set(lastMonthTotals):

        currentTotal = currentMonthTotals.get(description, float('0'))
        spanCurrentTotal = f'<span class="feed-current-total">{currentTotal:.2f}</span>'

        lastTotal = lastMonthTotals.get(description, float('0'))
        spanLastTotal = f'<span class="feed-last-total">{lastTotal:.2f}</span>'

        descriptionHTML = f'<span class="feed-description">{escape(description)}</span>'

        if lastTotal == 0 and currentTotal > 0:
            feed.append(f"You started spending on {descriptionHTML} this month: {spanCurrentTotal}")
        elif lastTotal > 0 and currentTotal > 0:
            change = currentTotal - lastTotal
            percent = (change / lastTotal) * 100 if lastTotal else 0
            spanPercent = f'<span class="feed-percent">{abs(percent):.1f}</span>'
            if abs(percent) >= 10:
                moreOrLess = (
                    f'<span class="feed-message-more">more</span>' if percent > 0 
                    else f'<span class="feed-message-less">less</span>'
                )
                feed.append(f"You have spent {spanPercent}% {moreOrLess} on {descriptionHTML} this month {spanCurrentTotal} compared to last month's {spanLastTotal}")
    if not feed:
        feed.append("No significant changes in your spending this month.")

    return JsonResponse({'feed': feed})

@login_required
def delete_transaction(request, transaction_id):
    if request.method == 'POST':
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        transaction.delete()
        return JsonResponse({'success': True, 'message': 'Transaction deleted successfully'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def bulk_delete_transactions(request):
    if request.method == 'POST':
        if request.POST.get('delete_all') == 'true':
            deleted_count = Transaction.objects.filter(user=request.user).count()
            Transaction.objects.filter(user=request.user).delete()
            return JsonResponse({
                'success': True,
                'message': f'{deleted_count} transaction(s) deleted successfully',
                'deleted_count': deleted_count
            })

        transaction_ids = request.POST.getlist('transaction_ids')
        deleted_count = 0

        if transaction_ids:
            try:
                valid_ids = [int(tid) for tid in transaction_ids if tid.isdigit()]

                if valid_ids:
                    deleted_transactions = Transaction.objects.filter(
                        id__in=transaction_ids,
                        user=request.user
                    )
                    deleted_count = deleted_transactions.count()
                    deleted_transactions.delete()
            
                    return JsonResponse({
                        'success': True,
                        'message': f'{deleted_count} transaction(s) deleted successfully',
                        'deleted_count': deleted_count
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'error': 'No valid transaction IDs provided'
                    })
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid transaction IDs provided'
                })
        
        return JsonResponse({
            'success': False, 
            'error': 'No transactions selected'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def home(request):
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date', '').strip()
            if not date_str:
                return JsonResponse({'success': False, 'error': 'Date is required!'})
            
            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format'})

            category = request.POST.get('category', '').strip()
            description = request.POST.get('description', '').strip()
            amount = request.POST.get('amount', '').strip()
            type_ = request.POST.get('type', '').strip()

            if not all([category, description, amount, type_]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})
            
            if not amount.replace('.', '').replace('-', '').isdigit():
                return JsonResponse({'success': False, 'error': 'Amount must be a valid number'})
            
            if type_ not in ['expense', 'income']:
                return JsonResponse({'success': False, 'error': 'Type must be expense or income'})
            
            transaction = Transaction.objects.create(
                user=request.user,
                date=date,
                category=category,
                description=description,
                amount=amount,
                type=type_
            )

            transaction.refresh_from_db()

            new_transaction = {
                'id': transaction.id,
                'date': date_str,
                'category': category,
                'description': description,
                'amount': amount,
                'type': type_
            }

            return JsonResponse({'success': True, 'transaction': new_transaction})

        except Exception as e:
            print(f"Error creating transaction: {e}")
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred'})
        
    search_query = request.GET.get('search', '').strip()
    all_transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    if search_query:
        filtered_transactions = [
            t for t in all_transactions
            if (search_query in str(t.date).lower() or
                search_query in t.category.lower() or
                search_query in t.description.lower() or
                search_query in str(t.amount).lower() or
                search_query in t.type.lower())
        ]
        filtered_transactions = sorted(filtered_transactions, key=lambda t: t.date, reverse=True)
    else:
        filtered_transactions = list(all_transactions)

    expense_count = Transaction.objects.filter(user=request.user, type='expense').count()
    income_count = Transaction.objects.filter(user=request.user, type='income').count()

    paginator = Paginator(filtered_transactions, 15)
    page_number = request.GET.get('page', 1)

    try:
        transactions_page = paginator.page(page_number)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)

    transactions_list = [
        {
            'id': t.id,
            'date': t.date,
            'category': t.category,
            'description': t.description,
            'amount': t.amount,
            'type': t.type
        }
        for t in transactions_page
    ]
    return render(request, 'core/home.html', {
        'transactions': transactions_list,
        'page_obj': transactions_page,
        'search_query': search_query,
        'expense_count': expense_count,
        'income_count': income_count
        })

@login_required
def predictions(request):
    transactions = Transaction.objects.filter(user=request.user)
    transactions_list = [
        {
            'id': t.id,
            'date': t.date.isoformat(),
            'category': t.category,
            'description': t.description,
            'amount': t.amount,
            'type': t.type
        }
        for t in transactions
    ]
    transactions_json = json.dumps(transactions_list)
    return render(request, 'core/predictions.html', {'transactions_json': transactions_json})

@login_required
def charts(request):
    transactions = Transaction.objects.filter(user=request.user)
    transactions_list = [
        {
            'id': t.id,
            'date': t.date.isoformat(),
            'category': t.category,
            'description': t.description,
            'amount': t.amount,
            'type': t.type
        }
        for t in transactions
    ]
    transactions_json = json.dumps(transactions_list)
    return render(request, 'core/charts.html', {'transactions_json': transactions_json})

@login_required
def generate_chart(request):
    chart_type = request.GET.get('type')
    year = request.GET.get('year')

    transactions = Transaction.objects.filter(user=request.user)

    if year:
        try:
            year = int(year)
            transactions = [t for t in transactions if t.date.year == year]
        except(ValueError, TypeError) as e:
            print(f"Year validation error: {e}, year value: {year}")
            return HttpResponse('Invalid year', status=400)
    else:
        print('No year provided, using all transactions')
        transactions = list(transactions)
    
    validChartTypes = [
        'bar', 'horizontalBar', 'surplusDeficit', 'savings', 'barByDate', 'monthlyCategorySplit'
    ]

    if chart_type not in validChartTypes:
        print(f"Invalid chart type: {chart_type}")
        return HttpResponse('Invalid chart type', status=400)

    try:
        chart_module = import_module(f'core.charts.{chart_type}')
        chart_func = getattr(chart_module, f'generate_{chart_type}_chart')
        image_base64 = chart_func(transactions, year)
    except(ImportError, AttributeError) as e:
        print(f"Error loading chart module for {chart_type}: {e}")
        return HttpResponse('Chart type not implemented', status=400)
    
    return HttpResponse(f'data:image/png;base64,{image_base64}', content_type='image/png')

@login_required
def generate_prediction(request):
    print("Received request with params:", request.GET)
    prediction_type = request.GET.get('type')
    monthsAmount = request.GET.get('monthsAmount', 12)
    n_future = int(request.GET.get('n_future', 1))

    try:
        monthsAmount = int(monthsAmount)
        if monthsAmount < 1:
            raise ValueError("Number of past months must be at least 1")
    except (ValueError, TypeError) as e:
        print(f"Invalid monthsAmount: {monthsAmount}, defaulting to 12")
        monthsAmount = 12

    transactions = Transaction.objects.filter(user=request.user)
    transactions = list(transactions)

    if not transactions:
        print("No transactions found for user")
        return HttpResponse('No transactions available for prediction', status=400)

    validPredictionModels = [
        'linear', 'polynomial', 'sarimax', 'randomforest', 'xgboost', 'ensemble'
    ]

    if prediction_type not in validPredictionModels:
        print(f"Invalid prediction tyoe: {prediction_type}")
        return HttpResponse('Invalid prediction type', status=400)
    
    try:
        prediction_module = import_module(f'core.prediction_models.{prediction_type}')
        prediction_func = getattr(prediction_module, f'{prediction_type}Model')
        model_instance = prediction_func(transactions=transactions, n_future_months=n_future)
        results = model_instance.predict()

        if not isinstance(results, tuple):
            predictions = [results]
            months = model_instance.months
            y = model_instance.y
            best_mse = None
        else:
            predictions, months, y, best_mse = results

        image_base64 = generate_prediction_plot(months, y, predictions, monthsAmount=monthsAmount, mse=best_mse)

        return HttpResponse(f'data:image/png;base64,{image_base64}', content_type='image/png')
    except(ImportError, AttributeError) as e:
        print(f"Error loading prediction module for {prediction_type}: {e}")
        return HttpResponse('Chart type not implemented', status=400)
    except ValueError as e:
        return HttpResponse(str(e), status=400)
    except Exception as e:
        print(f"Prediction Error: {e}")
        return HttpResponse('Error generating prediction', status=500)

class exportPDFView(View):
    def get(self, request):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)

        data = [['Date', 'Category', 'Description', 'Amount', 'Type']]
        transactions = Transaction.objects.filter(user=request.user).values('date', 'category', 'description', 'amount', 'type')
        for t in transactions:
            data.append([str(t['date']), t['category'], t['description'], t['amount'], t['type']])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#C81400'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#ecf0f1'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ]))

        elements = [table]
        doc.build(elements)

        buf.seek(0)
        pdf = buf.getvalue()
        buf.close()

        date = datetime.datetime.now().strftime('%Y-%m-%d')

        response = HttpResponse(content_type ='application.pdf')
        response['Content-Disposition'] = f'attachment; filename="transactions_export{date}.pdf"'
        response.write(pdf)
        return response

class exportCSVView(View):
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user).values('date', 'category', 'description', 'amount', 'type')

        date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transactions_export{date}.csv'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Category', 'Description', 'Amount', 'Type'])

        for t in transactions:
            writer.writerow([str(t['date']), t['category'], t['description'], t['amount'], t['type']])
        return response
    
@login_required
def import_csv(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'No file uploaded')
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')
        
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File must be a CSV')
            return JsonResponse({'success': False, 'error': 'File must be a CSV'}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')
        
        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            expected_headers = ['Date', 'Category', 'Description', 'Amount', 'Type']
            if not all(header in reader.fieldnames for header in expected_headers):
                messages.error(request, 'Invalid CSV headers')
                return JsonResponse({'success': False, 'error': 'Invalid CSV headers'}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')
            
            imported_count = 0
            errors = []
            transactions = []

            for row in reader:
                try:
                    date_str = row['Date'].strip()
                    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    category = row['Category'].strip()
                    description = row['Description'].strip()
                    amount = row['Amount'].strip()
                    type_ = row['Type'].strip()

                    if not all([category, description, amount, type]):
                        errors.append(f"Missing fields in row: {row}")
                        continue

                    if not amount.replace('.', '').replace('-', '').isdigit():
                        errors.append(f"Invalid amount in row: {row}")
                        continue

                    if type_ not in ['expense', 'income']:
                        errors.append(f"Invalid type in row: {row}")
                        continue

                    transactions.append({
                        'date': date,
                        'category': category,
                        'description': description,
                        'amount': amount,
                        'type': type_
                    })
                except ValueError as e:
                    errors.append(f"Invalid date format in row: {row}")
                    continue
                except Exception as e:
                    errors.append(f"Error processing row: {row}")
                    continue

            transactions.sort(key=lambda x: x['date'])

            for transaction in transactions:
                try:
                    transaction_obj, created = Transaction.objects.get_or_create(
                        user=request.user,
                        date=transaction['date'],
                        category=transaction['category'],
                        description=transaction['description'],
                        amount=transaction['amount'],
                        type=transaction['type']
                    )
                    if created:
                        imported_count += 1
                except Exception as e:
                    errors.append(f"Error saving transaction: {transaction}")
                    continue

            response_data = {
                'success': True,
                'message': f'{imported_count} transaction(s) imported successfully',
                'imported_count': imported_count
            }
            if errors:
                response_data['errors'] = errors
            messages.success(request, response_data['message'])
            if errors:
                messages.warning(request, f"Some rows could not be imported: {', '.join(errors)}")
            return JsonResponse(response_data) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')
        
        except Exception as e:
            messages.error(request, f'Error processing CSV: {str(e)}')
            return JsonResponse({'success': False, 'error': f'Error processing CSV: {str(e)}'}, status=500) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')

    messages.error(request, 'Invalid request method')
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('home')