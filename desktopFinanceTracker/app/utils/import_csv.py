import csv
from datetime import datetime
from database.db import insertTransaction

def import_csv(user_id, file_path):
    imported_count = 0
    errors = []

    if file_path is None:
        return 0, ['No file selected']
    
    if not isinstance(file_path, str):
        return 0, ['Invalid file path']

    if not file_path.endswith('.csv'):
        return 0, ['File must be a CSV']

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            expected_headers = ['Date', 'Category', 'Description', 'Amount', 'Type']

            if not all(header in reader.fieldnames for header in expected_headers):
                return 0, ['Invalid CSV headers. Expected: ' + ', '.join(expected_headers)]
            
            transactions = []
        
            for row_num, row in enumerate(reader, start=2):
                try:
                    date_str = row['Date'].strip()
                    date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                    category = row['Category'].strip()
                    description = row['Description'].strip()
                    amount = row['Amount'].strip()
                    type_ = row['Type'].strip()

                    if not all([date, category, description, amount, type_]):
                        errors.append(f'Row {row_num}: Missing fields')
                        continue

                    if not amount.replace('.', '').replace('-', '').replace(',', '').isdigit():
                        errors.append(f'Row {row_num}: Invalid amount "{amount}"')
                        continue

                    if type_ not in ['expense', 'income']:
                        errors.append(f'Row {row_num}: Invalid type "{type_}"')
                        continue

                    transactions.append({
                        'date': date,
                        'category': category,
                        'description': description,
                        'amount': amount,
                        'type': type_
                    })
                except ValueError as ve:
                    errors.append(f'Row {row_num}: Invalid date "{date}"')
                    continue

            transactions.sort(key=lambda x: x['date'])

            for transaction in transactions:
                try:
                    _, created = insertTransaction(
                        date=transaction['date'],
                        category=transaction['category'],
                        description=transaction['description'],
                        amount=transaction['amount'],
                        type_=transaction['type'],
                        user_id=user_id
                    )
                    if created:
                        imported_count += 1
                except Exception as e:
                    errors.append(f'Error saving: {str(e)}')
                    continue

    except FileNotFoundError:
        return 0, [f'File not found: {file_path}']
    except Exception as e:
        return 0, [f'Error processing CSV: {str(e)}']
    
    return imported_count, errors