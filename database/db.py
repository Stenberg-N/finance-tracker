# Database

import sqlite3
import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def init_db():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            type TEXT DEFAULT 'expense'
        )
    ''')
    connect_to_database.commit()
    connect_to_database.close()

def insert_transaction(date, category, description, amount, type_):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('''
        INSERT INTO transactions (date, category, description, amount, type)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, category, description, amount, type_))

    connect_to_database.commit()
    connect_to_database.close()

def migrate_add_type_column():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute("ALTER TABLE transactions ADD COLUMN type TEXT DEFAULT 'expense'")
    connect_to_database.commit()
    connect_to_database.close()

def type_column_exists():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute("PRAGMA table_info(transactions)")
    columns = [info[1] for info in db_cursor.fetchall()]
    connect_to_database.close()
    return 'type' in columns

def view_all_transactions():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    connect_to_database.close()
    return rows

def view_transactions_by_month(month, year):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    search_pattern = f'%-{month:02d}-{year}'
    db_cursor.execute('SELECT * FROM transactions WHERE date LIKE ?', (search_pattern,))
    rows = db_cursor.fetchall()
    connect_to_database.close()
    return rows

def view_transactions_by_week(week, year):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    try:
        start_date = datetime.datetime.strptime(f'{year}-W{week - 1}-1', "%Y-W%W-%w").date()
        end_date = start_date + datetime.timedelta(days=6)
    except Exception:
        connect_to_database.close()
        return []
    
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

    connect_to_database.close()
    return filtered

def clear_all_transactions():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('DELETE FROM transactions')
    connect_to_database.commit()
    connect_to_database.execute('VACUUM')
    connect_to_database.close()

def backup_db():
    connect_to_database = sqlite3.connect(config.db_path)
    db_backup_conn = sqlite3.connect(config.db_backup_path)
    connect_to_database.backup(db_backup_conn)
    connect_to_database.close()
    db_backup_conn.close()