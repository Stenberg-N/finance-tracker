# Finance tracker

from database.db import init_db, insert_transaction, view_all_transactions, view_transactions_by_month, view_transactions_by_week, clear_all_transactions
from exports import export_transactions_to_csv, export_transactions_to_excel, export_transactions_to_pdf
import os
import config

script_directory = os.path.dirname(os.path.abspath(__file__))
config.db_path = os.path.join(script_directory, 'database', 'finance.db')
config.exports_path = os.path.join(script_directory, 'exports')

init_db()

while True:
    print("\n1. Add transaction")
    print("2. View all transactions")
    print("3. View transactions by month")
    print("4. View transactions by week")
    print("5. Export transactions")
    print("6. Clear all transactions")
    print("7. Exit")
    choice = input("Choose option: ")

    if choice == '1':
        insert_transaction()
    elif choice == '2':
        view_all_transactions()
    elif choice == '3':
        view_transactions_by_month()
    elif choice == '4':
        view_transactions_by_week()
    elif choice == '5':
        print("Export data as 1) CSV, 2) Excel, 3) PDF")
        exportchoice = input("Choose export format: ")
        if exportchoice == '1':
            export_transactions_to_csv()
        elif exportchoice == '2':
            export_transactions_to_excel()
        elif exportchoice == '3':
            export_transactions_to_pdf()
    elif choice == '6':
        print("Are you sure you want to delete all of your data?")
        final_choice = input("If you are, write 'delete my data'. If not, input the letter 'n' and press enter: ")
        if final_choice.lower() == 'delete my data':
            clear_all_transactions()
        else:
            print("Your data has not been removed.")
            continue
    elif choice == '7':
        break
    else:
        print("Invalid input.")