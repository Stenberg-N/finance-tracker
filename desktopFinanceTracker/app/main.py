from database.db import initDB
from app.application import Application
from app.config import DB_PATH
import matplotlib, multiprocessing
matplotlib.use('TkAgg')

if __name__ == "__main__":
    multiprocessing.freeze_support()
    DB_PATH.parent.mkdir(exist_ok=True)
    initDB()
    app = Application()
    app.mainloop()