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

def view_transaction():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    print("\n=== Transaction history ===")
    for row in rows:
        print(row)
    connect_to_database.close()

init_db()

while True:
    print("\n1. Add transaction")
    print("2. View transactions")
    print("3. Exit")
    choice = input("Choose option: ")

    if choice == '1':
        insert_transaction()
    elif choice == '2':
        view_transaction()
    elif choice == '3':
        break
    else:
        print("Invalid input.")