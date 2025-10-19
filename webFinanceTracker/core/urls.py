from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import customLoginView, RegisterView, exportPDFView, exportCSVView

urlpatterns = [
    path('', login_required(views.home), name='home'),
    path('charts/', login_required(views.charts), name='charts'),
    path('predictions/', login_required(views.predictions), name='predictions'),
    path('delete/<int:transaction_id>/', login_required(views.delete_transaction), name='delete_transaction'),
    path('bulk-delete/', login_required(views.bulk_delete_transactions), name='bulk_delete_transactions'),
    path('login/', customLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('generate-chart/', login_required(views.generate_chart), name='generate_chart'),
    path('generate-prediction/', login_required(views.generate_prediction), name='generate_prediction'),
    path('export-pdf/', exportPDFView.as_view(), name='export_pdf'),
    path('export-csv/', exportCSVView.as_view(), name='export_csv'),
    path('import-csv/', login_required(views.import_csv), name='import_csv'),
    path('analytics/', login_required(views.analytics), name='analytics'),
    path('feed-messages/', login_required(views.generate_feed_messages), name='feed_messages')
]