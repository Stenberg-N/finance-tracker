# Finance tracker

import sqlite3
import os

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

def view_transaction_by_month():
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
    print("2. View transactions")
    print("3. View transactions by month")
    print("4. Clear all transactions")
    print("5. Exit")
    choice = input("Choose option: ")

    if choice == '1':
        insert_transaction()
    elif choice == '2':
        view_all_transactions()
    elif choice == '3':
        view_transaction_by_month()
    elif choice == '4':
        print("Are you sure you want to delete all of your data?")
        final_choice = input("If you are, input the letter 'y'. If not, input the letter 'n' and press enter: ")
        if final_choice.lower() == 'y':
            clear_all_transactions()
        else:
            print("Your data has not been removed.")
            continue
    elif choice == '5':
        break
    else:
        print("Invalid input.")