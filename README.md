# Finance Tracker

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-purple.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Latest Release](https://img.shields.io/github/v/release/Stenberg-N/finance-tracker?label=Desktop)](https://github.com/Stenberg-N/finance-tracker/releases)

A personal finance tracker with data visualizations, machine learning models for expense predictions, import and export functionality, and a transaction feed to reflect changes in your transactions. Available for desktop and web. A demo is also available and hosted at Northflank with login credentials for you to test the app with. Built to help users monitor spending and forecast budgets.

## Features
- **Data Visualization**: Multiple charts including simple pie, donut and bar charts to stacked bar, TOP 5 and cumulative charts.
- **Machine Learning Models**: Linear, Polynomial, Random Forest, XGBoost, SARIMAX models + ensemble model where Linear, Polynomial, XGBoost and SARIMAX models are combined.
- **Data Management**: Import data in CSV and export in CSV, PDF and Excel (Web app does not support exporting in Excel).
- **Transaction Feed**: Monitors your spending and compares your accumulated expenses in the current month to last month's and gives you insight if you have started spending on something new or if you have spent less or more on a specific category (e.g. electricity, groceries).
- **User Authentication and Encryption**: Your transaction data is encrypted. Both versions require an account. The desktop version supports multiple users sharing the system. Your data will reside in your user's Local folder inside AppData, which is specific for each user, so other users won't be able to access it if not logged in as you.

## Screenshots
### Web App Home Screen
<img width="3439" height="1322" alt="mainscreen" src="https://github.com/user-attachments/assets/cfd52317-3427-4ef6-a2fc-073dac30993d" />

### Desktop Home Screen
<img width="3439" height="1417" alt="desktop_homescreen" src="https://github.com/user-attachments/assets/95bc013e-6972-4667-9f18-464e771d0a94" />

### Desktop Transaction Table
<img width="1600" height="975" alt="desktop_data_table" src="https://github.com/user-attachments/assets/c1f478bd-1622-4264-ac6c-83b4abc9b903" />

### Desktop Transaction Feed
<img width="771" height="824" alt="desktop_transaction_feed" src="https://github.com/user-attachments/assets/c4554445-9c90-4e0d-b45d-5b6a19e4b67b" />

### Linear ML Model 
<img width="2357" height="1164" alt="linear_model" src="https://github.com/user-attachments/assets/151785be-3a3d-4639-83bc-f7a5d021b74f" />

### Cumulative Savings Chart
<img width="2357" height="1167" alt="savings_chart" src="https://github.com/user-attachments/assets/8d5058f5-e0f8-40cc-9b34-869b1059bbc2" />

### Stacked Bar Chart
<img width="3189" height="1323" alt="stackerbar_chart" src="https://github.com/user-attachments/assets/5c5bdd03-69a7-49d1-8549-89ede40d6df0" />

### Web App's TOP 5
<img width="3187" height="1177" alt="top5" src="https://github.com/user-attachments/assets/16ec1640-0889-4a97-95a8-515e7583a289" />

### Web App's Donut Chart
<img width="1142" height="1177" alt="donut" src="https://github.com/user-attachments/assets/419f6193-9fea-4c6c-81ce-b201361345b6" />

## Demo
Try the web version at [Northflank](https://site--financetracker-app--kwlb8kg8h4nw.code.run/).
The demo credentials are on the login page, plus here:
```text
Username: demo
Password: ?thisIsAdemo
```
When logging on the account, it will take a few seconds since it is loading the demo data to the account. Note: The account is reset every hour.

## Installation
### Web Version
1. Clone the repository:
```text
git clone https://github.com/Stenberg-N/finance-tracker.git
cd finance-tracker/webFinanceTracker
```
2. Set up a virtual environment:
```text
python -m venv venv
venv/Scripts/activate
```
3. Install dependencies:
```text
pip install -r requirements.txt
```
4. Create a Django SECRET_KEY and DATA_ENCRYPTION_KEY:<br>
The SECRET_KEY:
```text
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
The DATA_ENCRYPTION_KEY:
```text
python -c "import os; import base64; new_key = base64.urlsafe_b64encode(os.urandom(32)); print(new_key)"
```
Or you can use e.g. the secrets module and create longer keys if that's something you wish:
```text
python -c "import secrets; new_key = secrets.token_hex(100); print(new_key)"
```
5. Create a .env file to the root directory (webFinanceTracker/) and add three variables in it:
```text
DJANGO_ENV=development
DJANGO_SECRET_KEY=your secret key you printed
DATA_ENCRYPTION_KEY=your data encryption key you printed
```
6. Apply migrations and start the server:
```text
python manage.py migrate
python manage.py runserver
```
7. Access at http://localhost:8000

### Desktop Version
The desktop app is a standalone Python executable packaged with PyInstaller. No installation required beyond downloading.
1. Download the latest release from [GitHub Releases](https://github.com/Stenberg-N/finance-tracker/releases).
2. Extract the ZIP file.
3. Run the executable: FinanceTracker.exe
4. Register and make an account
5. Login to your account

## Usage
- **Adding Transactions**: Use the form on the home page or import from files.
- **Viewing Charts**: Navigate to the Charts tab on the sidebar, fill the inputs and press generate.
- **Running Predictions**: Navigate to the Predictions tab on the sidebar, select you model, fill the inputs and press generate.
- **Exporting**: Exporting is done on the Home screen. The Desktop version uploads the exports to C:\Users\YourUsename\AppData\Local\Stenberg-N\desktopFinanceTracker\. Here also resides the database.

## Technologies
- **Backend**: Django (web), pure Python (desktop).
- **Frontend**: HTML/CSS/JS (web), customTkinter and Tkinter (desktop).
- **Data Visualization**: Chart.js and Matplotlib (web), only Matplotlib (desktop).
- **Machine Learning**: Scikit-learn, Optuna, XGBoost, SARIMAX.
- **Database**: SQLite (default), PostgreSQL (production).
- **Packaging**: PyInstaller for desktop builds.

## Other important points
Like previously mentioned, the path for the database and exports is:<br>
C:\Users\YourUsename\AppData\Local\Stenberg-N\desktopFinanceTracker\

If you want to import from a CSV it needs a specific format and these exact headers:<br>
Date, Category, Description, Amount and Type<br>
<br>
An example of a CSV that the app accepts:
```text
Date,Category,Description,Amount,Type
2021-10-18,Salary,Employer paycheck,3067.54,income
2021-10-23,Bills,Electricity bill,42.09,expense
...
```

## License
This project is licensed under the GNU General Public License Version 3 (GNU GPLv3). See the LICENSE file for details.
