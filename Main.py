# Finance tracker

import sqlite3
import os
import datetime

script_directory = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_directory, 'finance.db')

exports_path = os.path.join(script_directory, 'exports')
if not os.path.exists(exports_path):
    os.makedirs(exports_path)

def init_db():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL

        )
    ''')
    connect_to_database.commit()
    connect_to_database.close()

def insert_transaction():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    
    date = input("Enter the date (DD-MM-YYYY): ")
    category = input("Enter the category (e.g. Food, Bills): ")
    description = input("Description: ")
    amount = float(input("Enter the amount: "))

    db_cursor.execute('''
        INSERT INTO transactions (date, category, description, amount)
        VALUES (?, ?, ?, ?)
    ''', (date, category, description, amount))

    connect_to_database.commit()
    connect_to_database.close()

def view_all_transactions():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    print("\n=== Transaction history ===")
    for row in rows:
        print(row)
    connect_to_database.close()

def view_transactions_by_month():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    month_year = input("Enter month and year (MM-YYYY): ")
    search_pattern = f'%-{month_year}'
    db_cursor.execute('SELECT * FROM transactions WHERE date LIKE ?', (search_pattern,))
    rows = db_cursor.fetchall()
    print(f"\n=== Transaction history for {month_year} ===")
    if not rows:
        print("No transactions found for this period.")
    else:
        for row in rows:
            print(row)
    connect_to_database.close()

def view_transactions_by_week():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    week_year = input("Enter the week and the year (WW-YYYY):  ")
    try:
        week, year = map(int, week_year.split('-'))
        start_date = datetime.datetime.strptime(f'{year}-W{week - 1}-1', "%Y-W%W-%w").date()
        end_date = start_date + datetime.timedelta(days=6)
    except Exception:
        print("Invalid input. Please use the format WW-YYYY (e.g. 12-2025).")
        return
    
    start_str = start_date.strftime("%d-%m-%Y")
    end_str = end_date.strftime("%d-%m-%Y")

    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    filtered = []
    for row in rows:
        try:
            row_date = datetime.datetime.strptime(row[1], "%d-%m-%Y").date()
            if start_date <= row_date <= end_date:
                filtered.append(row)
        except Exception:
            continue

    print(f"\n=== Transaction history for week {week} of {year} ({start_str} to {end_str}) ===")
    if not filtered:
        print("No transactions found for this week.")
    else:
        for row in filtered:
            print(row)
    connect_to_database.close()

def clear_all_transactions():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('DELETE FROM transactions')
    connect_to_database.commit()
    connect_to_database.execute('VACUUM')
    connect_to_database.close()
    print("All transactions have been deleted and the database file has been compacted.")

init_db()

while True:
    print("\n1. Add transaction")
    print("2. View all transactions")
    print("3. View transactions by month")
    print("4. View transactions by week")
    print("5. Clear all transactions")
    print("6. Exit")
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
        print("Are you sure you want to delete all of your data?")
        final_choice = input("If you are, input the letter 'y'. If not, input the letter 'n' and press enter: ")
        if final_choice.lower() == 'y':
            clear_all_transactions()
        else:
            print("Your data has not been removed.")
            continue
    elif choice == '6':
        break
    else:
        print("Invalid input.")