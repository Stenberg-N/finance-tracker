from database.db import initDB
from app.application import Application
from app.config import DB_PATH

if __name__ == "__main__":
    DB_PATH.parent.mkdir(exist_ok=True)
    initDB()
    app = Application()
    app.mainloop()