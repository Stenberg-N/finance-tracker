# Database

import os
import sqlite3
import datetime

script_directory = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_directory, 'finance.db')

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
    
    while True:
        date = input("Enter the date (DD-MM-YYYY): ")
        try:
            datetime.datetime.strptime(date, "%d-%m-%Y")
            break
        except ValueError:
            print("Invalid input. Please use the format DD-MM-YYYY (e.g. 31-01-2025).")

    category = input("Enter the category (e.g. Food, Bills): ")
    description = input("Description: ")
    amount = float(input("Enter the amount. In case of decimals use dot(.) instead of comma(,): "))

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