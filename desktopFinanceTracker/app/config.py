from pathlib import Path
import os, appdirs

APP_NAME = 'desktopFinanceTracker'
APP_AUTHOR = 'Stenberg-N'

USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
os.makedirs(USER_DATA_DIR, exist_ok=True)

DB_DIR = os.path.join(USER_DATA_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)

EXPORTS_DIR = os.path.join(USER_DATA_DIR, 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

DB_PATH = Path(DB_DIR) / 'finance.db'
DB_BACKUP_PATH = Path(DB_DIR) / 'backup_finance.db'
EXPORTS_PATH = Path(EXPORTS_DIR)