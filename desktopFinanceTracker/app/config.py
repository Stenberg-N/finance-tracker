from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

DB_DIR = ROOT_DIR / 'database'
EXPORTS_DIR = ROOT_DIR / 'exports'

DB_PATH = DB_DIR / 'finance.db'
DB_BACKUP_PATH = DB_DIR / 'backup_finance.db'
EXPORTS_PATH = EXPORTS_DIR