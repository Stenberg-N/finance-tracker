# Database

import sqlite3
import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

encryption_key = None

def init_db():
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.executescript('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT,
            category TEXT,
            description TEXT,
            amount TEXT,
            type TEXT DEFAULT 'expense',
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            salt BLOB NOT NULL
        )
    ''')
    connect_to_database.commit()
    connect_to_database.close()

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def derive_key(password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=None)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def set_encryption_key(key: bytes):
    global encryption_key
    encryption_key = key

def clear_encryption_key():
    global encryption_key
    encryption_key = None

def verify_login(username, password):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
    result = db_cursor.fetchone()
    connect_to_database.close()
    if result:
        password_hash, salt = result
        if bcrypt.checkpw(password.encode(), password_hash):
            key, _ = derive_key(password, salt)
            set_encryption_key(key)
            return True

    clear_encryption_key()
    return False

def insert_user(username, password):
    try:
        connect_to_database = sqlite3.connect(config.db_path)
        db_cursor = connect_to_database.cursor()
        password_hash = hash_password(password)
        key, salt = derive_key(password)
        db_cursor.execute('INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)', (username, password_hash, salt))
        connect_to_database.commit()
        connect_to_database.close()
        return True, None
    except sqlite3.IntegrityError():
        connect_to_database.close()
        return False, "Username already exists!"
    except Exception as e:
        connect_to_database.close()
        return False, f"Registration failed: {str(e)}"

def get_user_id(username):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = db_cursor.fetchone()
    connect_to_database.close()
    return result[0] if result else None

def delete_user(username, password):
    try:
        connect_to_database = sqlite3.connect(config.db_path)
        db_cursor = connect_to_database.cursor()
        db_cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        result = db_cursor.fetchone()
        if not result:
            connect_to_database.close()
            return False, "User not found!"
        user_id, stored_hash = result
        if not bcrypt.checkpw(password.encode(), stored_hash):
            connect_to_database.close()
            return False, "Incorrect password!"

        db_cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        db_cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        connect_to_database.commit()
        connect_to_database.close()
        return True, "User and associated data deleted successfully!"
    except sqlite3.DatabaseError as e:
        connect_to_database.close()
        return False, f"Database error: {str(e)}"
    except Exception as e:
        connect_to_database.close()
        return False, f"Deletion failed: {str(e)}"

def insert_transaction(date, category, description, amount, type_, user_id):
    global encryption_key
    if encryption_key is None:
        raise ValueError("Encryption key is not set. Please log in.")
    fernet = Fernet(encryption_key)
    encrypted_date = fernet.encrypt(date.encode()).decode()
    encrypted_category = fernet.encrypt(category.encode()).decode()
    encrypted_description = fernet.encrypt(description.encode()).decode()
    encrypted_amount = fernet.encrypt(str(amount).encode()).decode()
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('''
        INSERT INTO transactions (date, category, description, amount, type, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (encrypted_date, encrypted_category, encrypted_description, encrypted_amount, type_, user_id))

    connect_to_database.commit()
    connect_to_database.close()

def view_all_transactions(user_id):
    global encryption_key
    if encryption_key is None:
        raise ValueError("Encryption key is not set. Please log in.")
    fernet = Fernet(encryption_key)
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT id, date, category, description, amount, type FROM transactions WHERE user_id = ?', (user_id,))
    rows = db_cursor.fetchall()
    connect_to_database.close()
    decrypted_rows = []
    for row in rows:
        try:
            decrypted_date = fernet.decrypt(row[1].encode()).decode()
            decrypted_category = fernet.decrypt(row[2].encode()).decode()
            decrypted_description = fernet.decrypt(row[3].encode()).decode()
            decrypted_amount = float(fernet.decrypt(row[4].encode()).decode())
            decrypted_rows.append((row[0], decrypted_date, decrypted_category, decrypted_description, decrypted_amount, row[5]))
        except Exception:
            continue
    return decrypted_rows

def view_transactions_by_month(month, year, user_id):
    global encryption_key
    if encryption_key is None:
        raise ValueError("Encryption key is not set. Please log in.")
    fernet = Fernet(encryption_key)
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT id, date, category, description, amount, type FROM transactions WHERE user_id = ?', (user_id,))
    rows = db_cursor.fetchall()
    connect_to_database.close()
    decrypted_rows = []
    for row in rows:
        try:
            decrypted_date = fernet.decrypt(row[1].encode()).decode()
            date_obj = datetime.datetime.strptime(decrypted_date, "%d-%m-%Y")
            if date_obj.month == month and date_obj.year == year:
                decrypted_category = fernet.decrypt(row[2].encode()).decode()
                decrypted_description = fernet.decrypt(row[3].encode()).decode()
                decrypted_amount = float(fernet.decrypt(row[4].encode()).decode())
                decrypted_rows.append((row[0], decrypted_date, decrypted_category, decrypted_description, decrypted_amount, row[5]))
        except Exception:
            continue
    return decrypted_rows

def view_transactions_by_week(week, year, user_id):
    global encryption_key
    if encryption_key is None:
        raise ValueError("Encryption key is not set. Please log in.")
    fernet = Fernet(encryption_key)
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    try:
        start_date = datetime.datetime.strptime(f'{year}-W{week - 1}-1', "%Y-W%W-%w").date()
        end_date = start_date + datetime.timedelta(days=6)
    except Exception:
        connect_to_database.close()
        return []
    
    db_cursor.execute('SELECT id, date, category, description, amount, type FROM transactions WHERE user_id = ?', (user_id,))
    rows = db_cursor.fetchall()
    connect_to_database.close()
    decrypted_rows = []
    for row in rows:
        try:
            decrypted_date = fernet.decrypt(row[1].encode()).decode()
            row_date = datetime.datetime.strptime(decrypted_date, "%d-%m-%Y").date()
            if start_date <= row_date <= end_date:
                decrypted_category = fernet.decrypt(row[2].encode()).decode()
                decrypted_description = fernet.decrypt(row[3].encode()).decode()
                decrypted_amount = float(fernet.decrypt(row[4].encode()).decode())
                decrypted_rows.append((row[0], decrypted_date, decrypted_category, decrypted_description, decrypted_amount, row[5]))
        except Exception:
            continue
    return decrypted_rows

def clear_all_transactions(user_id):
    connect_to_database = sqlite3.connect(config.db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    connect_to_database.commit()
    connect_to_database.execute('VACUUM')
    connect_to_database.close()

def backup_db():
    connect_to_database = sqlite3.connect(config.db_path)
    db_backup_conn = sqlite3.connect(config.db_backup_path)
    connect_to_database.backup(db_backup_conn)
    connect_to_database.close()
    db_backup_conn.close()