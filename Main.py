# Finance tracker

from database.db import init_db, insert_transaction, view_all_transactions, view_transactions_by_month, clear_all_transactions, backup_db, verify_login, get_user_id, insert_user, delete_user, clear_encryption_key, \
    delete_transactions_by_id
from exports import export_transactions_to_csv, export_transactions_to_excel, export_transactions_to_pdf
import os
import config
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import datetime
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from ml import linear_model, polynomial_model, sarimax_model, randomforest_model, ensemble_model, xgboost_model
import threading

current_user = None

script_directory = os.path.dirname(os.path.abspath(__file__))
config.db_path = os.path.join(script_directory, 'database', 'finance.db')
config.db_backup_path = os.path.join(script_directory, 'database', 'backup_finance.db')
config.exports_path = os.path.join(script_directory, 'exports')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Finance Tracker")
app.geometry("1600x900")

PREDICTION_MODEL_DESCRIPTIONS = {
    'linear': "Linear Regression including Ridge, Lasso and Robust techniques: Best for data with a linear trend. Automatically selects the best regularized or robust linear model.",
    'polynomial': "Polynomial Regression including Ridge, Lasso and Robust techniques for overfitting and/or outliers: Captures non-linear trends. Useful if your expenses have curves or seasonal effects.",
    'sarimax': "SARIMAX: Time series model. Good for data with trends and seasonality.",
    'randomforest': "Random Forest: Combines many decision trees to make better predictions, even with complex or unusual data.",
    'ensemble': "Ensemble: Combines multiple models for improved accuracy and robustness.",
    'xgboost': "XGBoost: A powerful and efficient gradient boosting algorithm. Excels at capturing complex patterns and interactions in data, often delivering top performance in prediction tasks. Well-suited for both small and large datasets."
}

CHART_DESCRIPTIONS = {
    'pie': "A basic pie chart.",
    'bar': "Displays all transactions in a bar plot.",
    'donut': "A basic donut chart.",
    'horizontal bar': "Lists the top 5 expenses by category and their description.",
    'surplus deficit': "Subtracts expenses from income on a monthly basis and shows whether profit or loss was made.",
    'savings': "Displays the trend of your transactions. Also shows if you are in the negative. May act in a bizarre way if stating a year to generate a chart from. This chart is mainly for a long period, so it is suggested to leave the year empty.",
    'bar by date_amount': "Displays both income and expenses per month.",
    'monthly category split': "Displays monthly expenses split by category and description."
}

CHART_LABELS = {
    'pie': "Pie Chart",
    'bar': "Bar plot of all transactions",
    'donut': "Donut Chart",
    'horizontal bar': "Top 5 expenses",
    'surplus deficit': "Surplus/Deficit chart",
    'savings': "Cumulative savings chart",
    'bar by date_amount': "Monthly transactions chart",
    'monthly category split': "Stacked bar chart"
}

class tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left", background="#ffffe0", relief="solid", borderwidth=1, font=("tahoma", "10", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

button_frame = ctk.CTkFrame(app, corner_radius=0)
button_frame.pack(side=ctk.LEFT, fill=ctk.Y, anchor=ctk.N)

linear_regression_btn = ctk.CTkButton(button_frame, text="Linear", command=lambda: show_prediction('linear'))
tooltip(linear_regression_btn, "Automatically select the best linear model: standard, Ridge (L2), Lasso (L1) or robust regression for your data.")
poly_regression_btn = ctk.CTkButton(button_frame, text="Polynomial", command=lambda: show_prediction('polynomial'))
tooltip(poly_regression_btn, "Captures non-linear treds. Useful if your expenses have curves or seasonal effects.")
sarimax_btn = ctk.CTkButton(button_frame, text="SARIMAX", command=lambda: show_prediction('sarimax'))
tooltip(sarimax_btn, "Time series model. Good for data with trends and seasonality.")
randomforest_btn = ctk.CTkButton(button_frame, text="RandomForest", command=lambda: show_prediction('randomforest'))
tooltip(randomforest_btn, "Combines many decision trees to make better predictions even with complex or unusual data.")
ensemble_btn = ctk.CTkButton(button_frame, text="Ensemble", command=lambda: show_prediction('ensemble'))
tooltip(ensemble_btn, "Combines the Linear, SARIMAX, Random Forest and XGBoost models for improved accuracy and robustness.")
xgboost_btn = ctk.CTkButton(button_frame, text="XGBoost", command=lambda: show_prediction('xgboost'))
tooltip(xgboost_btn, "Captures complex patterns and interactions in data. Suitable for small and large datasets.")
linear_regression_btn.pack_forget()
poly_regression_btn.pack_forget()
sarimax_btn.pack_forget()
randomforest_btn.pack_forget()
ensemble_btn.pack_forget()
xgboost_btn.pack_forget()

content_frame = ctk.CTkFrame(app, corner_radius=0)
content_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def clear_login_frame():
    for widget in login_frame.winfo_children():
        widget.destroy()

def clear_session():
    global current_user
    current_user = None
    clear_encryption_key()
    login_frame.pack(fill=ctk.BOTH, expand=True)
    content_frame.pack_forget()
    button_frame.pack_forget()
    show_login_screen()

def toggle_prediction_model_buttons():
    if linear_regression_btn.winfo_ismapped():
        linear_regression_btn.pack_forget()
        poly_regression_btn.pack_forget()
        sarimax_btn.pack_forget()
        randomforest_btn.pack_forget()
        ensemble_btn.pack_forget()
        xgboost_btn.pack_forget()
    else:
        linear_regression_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        poly_regression_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        sarimax_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        randomforest_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        ensemble_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        xgboost_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)

login_frame = ctk.CTkFrame(app, corner_radius=0)
login_frame.pack(fill=ctk.BOTH, expand=True)

def show_register_screen():
    clear_content()
    clear_login_frame()
    login_frame.pack(fill=ctk.BOTH, expand=True)
    ctk.CTkLabel(login_frame, text="Register", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

    ctk.CTkLabel(login_frame, text="Username").pack(pady=5)
    username_entry = ctk.CTkEntry(login_frame)
    username_entry.pack()

    ctk.CTkLabel(login_frame, text="Password").pack(pady=5)
    password_entry = ctk.CTkEntry(login_frame, show="*")
    password_entry.pack()

    ctk.CTkLabel(login_frame, text="Confirm Password").pack(pady=5)
    confirm_password_entry = ctk.CTkEntry(login_frame, show="*")
    confirm_password_entry.pack()

    def register():
        username = username_entry.get()
        password = password_entry.get()
        confirm_password = confirm_password_entry.get()

        if not username or not password:
            error = ctk.CTkLabel(login_frame, text="Username and password cannot be empty!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        if password != confirm_password:
            error = ctk.CTkLabel(login_frame, text="Passwords do not match!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        success, message = insert_user(username, password)
        if success:
            success = ctk.CTkLabel(login_frame, text="Registration successful! Please log in.", text_color="green")
            success.pack()
            success.after(2000, lambda: show_login_screen())
        else:
            error = ctk.CTkLabel(login_frame, text=message, text_color="red")
            error.pack()
            error.after(2000, error.destroy)

    ctk.CTkButton(login_frame, text="Register", command=register).pack(pady=12)
    ctk.CTkButton(login_frame, text="Back to Login", command=show_login_screen).pack(pady=5)

def show_login_screen():
    clear_content()
    clear_login_frame()
    login_frame.pack(fill=ctk.BOTH, expand=True)
    content_frame.pack_forget()
    button_frame.pack_forget()

    ctk.CTkLabel(login_frame, text="Login", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
    ctk.CTkLabel(login_frame, text="Register and create an account or if you already have an account, please login.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

    ctk.CTkLabel(login_frame, text="Username").pack(pady=5)
    username_entry = ctk.CTkEntry(login_frame)
    username_entry.pack()

    ctk.CTkLabel(login_frame, text="Password").pack(pady=5)
    password_entry = ctk.CTkEntry(login_frame, show="*")
    password_entry.pack()

    def login():
        username = username_entry.get()
        password = password_entry.get()

        if verify_login(username, password):
            global current_user
            current_user = username
            login_frame.pack_forget()
            button_frame.pack(side=ctk.LEFT, fill=ctk.Y, anchor=ctk.N)
            content_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
            show_home_screen()
            success = ctk.CTkLabel(login_frame, text="Login Successful! Welcome, {username}!", text_color="green")
            success.pack()
            success.after(2000, success.destroy)
        else:
            error = ctk.CTkLabel(login_frame, text="Login Failed: Invalid username or password", text_color="red")
            error.pack()
            error.after(2000, error.destroy)

    ctk.CTkButton(login_frame, text="Login", command=login).pack(pady=12)
    ctk.CTkButton(login_frame, text="Register", command=show_register_screen).pack(pady=5)

def show_delete_user():
    clear_content()
    ctk.CTkLabel(content_frame, text="Delete Account", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

    ctk.CTkLabel(content_frame, text="Enter your password to confirm account deletion").pack(pady=5)
    password_entry = ctk.CTkEntry(content_frame, show="*")
    password_entry.pack()

    def confirm_user_deletion():
        password = password_entry.get()
        if not password:
            error = ctk.CTkLabel(content_frame, text="Please enter your password!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        success, message = delete_user(current_user, password)
        if success:
            clear_session()
            success = ctk.CTkLabel(login_frame, text=message, text_color="green")
            success.pack()
            success.after(2000, success.destroy)
        else:
            error = ctk.CTkLabel(login_frame, text=message, text_color="green")
            error.pack()
            error.after(2000, success.destroy)

    ctk.CTkButton(content_frame, text="Confirm Delete", command=confirm_user_deletion).pack(pady=10)
    ctk.CTkButton(content_frame, text="Cancel", command=show_home_screen).pack(pady=5)

def show_home_screen():
    clear_content()
    user_id = get_user_id(current_user)
    ctk.CTkLabel(content_frame, text="Home screen", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

    home_frame = ctk.CTkFrame(content_frame, corner_radius=0)
    home_frame.pack(fill="both", expand=True, padx=20, pady=20)

    info_frame = ctk.CTkFrame(home_frame, corner_radius=0)
    info_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

    feed_frame = ctk.CTkScrollableFrame(info_frame)
    feed_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="nsew")

    backup_info_frame = ctk.CTkFrame(info_frame, height=40)
    backup_info_frame.grid(row=1, column=0, padx=20, sticky="ew")
    backup_info_frame.grid_propagate(False)

    export_add_transaction_frame = ctk.CTkFrame(home_frame, corner_radius=0)
    export_add_transaction_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

    add_transaction_frame = ctk.CTkScrollableFrame(export_add_transaction_frame)
    add_transaction_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

    export_frame = ctk.CTkScrollableFrame(export_add_transaction_frame)
    export_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

    ctk.CTkLabel(feed_frame, text="This month's feed", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor=ctk.W, padx=20, pady=(10, 20))
    feed_messages = generate_feed_messages(user_id)
    for message in feed_messages:
        ctk.CTkLabel(feed_frame, text=message, wraplength=800, justify="left").pack(anchor=ctk.W, padx=10, pady=5)

    ctk.CTkLabel(export_frame, text="Export Transactions", font=ctk.CTkFont(size=24, weight="bold")).pack(padx=10, pady=(10, 0))
    ctk.CTkLabel(export_frame, text="Used to export data as CSV, Excel or PDF.", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 20))

    ctk.CTkLabel(export_frame, text="Filename:").pack()
    filename_entry = ctk.CTkEntry(export_frame)
    filename_entry.pack(pady=(0, 20))

    def export_to_csv():
        user_id = get_user_id(current_user)
        filename = filename_entry.get()
        export_transactions_to_csv(user_id, filename)
        success = ctk.CTkLabel(export_frame, text="Transactions were successfully exported to CSV!", font=ctk.CTkFont(size=12), text_color="green")
        success.pack()
        success.after(3000, success.destroy)

    ctk.CTkButton(export_frame, text="CSV", command=export_to_csv).pack(pady=10)

    def export_to_excel():
        user_id = get_user_id(current_user)
        filename = filename_entry.get()
        export_transactions_to_excel(user_id, filename)
        success = ctk.CTkLabel(export_frame, text="Transactions were successfully exported to Excel!", font=ctk.CTkFont(size=12), text_color="green")
        success.pack()
        success.after(3000, success.destroy)

    ctk.CTkButton(export_frame, text="Excel", command=export_to_excel).pack(pady=10)

    def export_to_pdf():
        user_id = get_user_id(current_user)
        filename = filename_entry.get()
        export_transactions_to_pdf(user_id, filename)
        success = ctk.CTkLabel(export_frame, text="Transactions were successfully exported to PDF!", font=ctk.CTkFont(size=12), text_color="green")
        success.pack()
        success.after(3000, success.destroy)

    ctk.CTkButton(export_frame, text="PDF", command=export_to_pdf).pack(pady=10)

    ctk.CTkLabel(add_transaction_frame, text="Add Transaction", font=ctk.CTkFont(size=24, weight="bold")).pack(padx=10, pady=(10, 0))
    ctk.CTkLabel(add_transaction_frame, text="Add income and expense transactions here to begin analysing and visualizing your data using the other features.", font=ctk.CTkFont(size=12), wraplength=300).pack(padx=10, pady=(0, 20))

    ctk.CTkLabel(add_transaction_frame, text="Type:").pack()
    type_var = ctk.StringVar(value="Select")
    type_option = ctk.CTkOptionMenu(add_transaction_frame, variable=type_var, values=["income", "expense"])
    type_option.pack(pady=(0, 20))

    ctk.CTkLabel(add_transaction_frame, text="Date (DD-MM-YYYY):").pack()
    date_entry = ctk.CTkEntry(add_transaction_frame)
    date_entry.pack()

    ctk.CTkLabel(add_transaction_frame, text="Category:").pack()
    category_entry = ctk.CTkEntry(add_transaction_frame)
    category_entry.pack()

    ctk.CTkLabel(add_transaction_frame, text="Description:").pack()
    description_entry = ctk.CTkEntry(add_transaction_frame)
    description_entry.pack()

    ctk.CTkLabel(add_transaction_frame, text="Amount:").pack()
    amount_entry = ctk.CTkEntry(add_transaction_frame)
    amount_entry.pack()

    def reset_add_transaction_form():
        date_entry.delete(0, ctk.END)
        category_entry.delete(0, ctk.END)
        description_entry.delete(0, ctk.END)
        amount_entry.delete(0, ctk.END)
        type_var.set("Select")

    def submit_data():
        date = date_entry.get()
        category = category_entry.get()
        description = description_entry.get()
        amount = amount_entry.get()
        user_id = get_user_id(current_user)

        try:
            amount = float(amount)
        except ValueError:
            error = ctk.CTkLabel(add_transaction_frame, text="Invalid amount!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        try:
            datetime.datetime.strptime(date, "%d-%m-%Y")
        except ValueError:
            error = ctk.CTkLabel(add_transaction_frame, text="Invalid date format!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        type_value = type_var.get()
        if type_value == "Select":
            error = ctk.CTkLabel(add_transaction_frame, text="Please select a type!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        insert_transaction(date, category, description, amount, type_value, user_id)
        success = ctk.CTkLabel(add_transaction_frame, text="Transaction was successfully added!", text_color="green")
        success.pack()
        success.after(2000, lambda: [success.destroy(), reset_add_transaction_form()])
        
    ctk.CTkButton(add_transaction_frame, text="Add", command=submit_data).pack(pady=(20, 10))

    def make_db_backup():
        confirmation = CTkMessagebox(title="Confirm Backup", message=f"Make a backup of the database?", icon="info", option_1="Cancel", option_2="Make a backup").get()
        if confirmation != "Make a backup":
            return

        backup_db()
        success = ctk.CTkLabel(backup_info_frame, text="Database has been successfully backed up! You can find it in the same file as the original database.", font=ctk.CTkFont(size=12), text_color="green")
        success.grid(row=0, column=1, pady=5, sticky="w")
        success.after(5000, success.destroy)

    ctk.CTkButton(info_frame, text="Backup DB", command=make_db_backup).grid(row=2, column=0, padx=20, pady=(5, 20), sticky="sw")
    ctk.CTkLabel(backup_info_frame, text="Backup results: ", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")

    home_frame.grid_columnconfigure(0, weight=3)
    home_frame.grid_columnconfigure(1, weight=2)
    home_frame.grid_rowconfigure(0, weight=1)

    info_frame.grid_rowconfigure(0, weight=50)
    info_frame.grid_rowconfigure(1, weight=1)
    info_frame.grid_rowconfigure(2, weight=0)
    info_frame.grid_columnconfigure(0, weight=1)

    export_add_transaction_frame.grid_rowconfigure(0, weight=4)
    export_add_transaction_frame.grid_rowconfigure(1, weight=2)
    export_add_transaction_frame.grid_columnconfigure(0, weight=1)

def generate_feed_messages(user_id):
    now = datetime.datetime.now()
    this_month = now.month
    this_year = now.year
    last_month = this_month - 1 if this_month > 1 else 12
    last_month_year = this_year if this_month > 1 else this_year - 1

    this_month_rows = view_transactions_by_month(this_month, this_year, user_id)
    last_month_rows = view_transactions_by_month(last_month, last_month_year, user_id)

    def combine(rows):
        description_totals = {}

        for row in rows:
            description = row[3]
            amount = row[4]
            transaction_type = row[5]
            if transaction_type == "expense":
                description_totals[description] = description_totals.get(description, 0) + abs(amount)
        return description_totals

    this_month_totals = combine(this_month_rows)
    last_month_totals = combine(last_month_rows)

    feed = []
    for description in set(this_month_totals) | set(last_month_totals):
        this_total = this_month_totals.get(description, 0)
        last_total = last_month_totals.get(description, 0)
        if last_total == 0 and this_total > 0:
            feed.append(f"You started spending on {description} this month: {this_total:.2f}€")
        elif last_total > 0:
            change = this_total - last_total
            percent = (change / last_total) * 100 if last_total else 0
            if abs(percent) >= 10:
                more_or_less = "more" if percent > 0 else "less"
                feed.append(f"You have spent {abs(percent):.1f}% {more_or_less} on {description} this month {this_total:.2f}€ compared to last month's {last_total:.2f}€")
    if not feed:
        feed.append("No significant changes in your spending this month.")
    return feed

def all_transactions_treeview():
    columns = ("c1", "c2", "c3", "c4", "c5", "c6")
    tree = tk.ttk.Treeview(content_frame, column=columns, show="headings")
    headers = ["ID", "Date", "Category", "Description", "Amount", "Type"]

    def treeview_sort_column(tv, col, col_index, reverse):
        data = [(tv.set(k, col), k) for k in tv.get_children("")]
        if col == "c2":
            try:
                data.sort(key=lambda t: datetime.datetime.strptime(t[0], "%d-%m-%Y"), reverse=reverse)
            except Exception:
                data.sort(reverse=reverse)
        else:
            try:
                data.sort(key=lambda t: float(t[0].replace(",", "").replace("€", "")), reverse=reverse)
            except ValueError:
                data.sort(reverse=reverse)
        for index, (val, k) in enumerate(data):
            tv.move(k, "", index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, col_index, not reverse))

    for idx, (col, header) in enumerate(zip(columns, headers)):
        tree.heading(col, text=header, command=lambda _col=col, _idx=idx: treeview_sort_column(tree, _col, _idx, False))
        tree.column(col, anchor=ctk.CENTER)

    tree.pack(expand=True, fill="both")
    return tree

def show_all_transactions_table():
    clear_content()
    ctk.CTkLabel(content_frame, text="All Transactions", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
    ctk.CTkLabel(content_frame, text="A table consisting of all your income and expense data.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

    searchbar_frame = ctk.CTkFrame(content_frame)
    searchbar_frame.pack(padx=20, pady=5, anchor=ctk.E)

    tree = all_transactions_treeview()
    user_id = get_user_id(current_user)
    all_rows = view_all_transactions(user_id)

    def fill_table(data):
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert("", ctk.END, values=row)

    fill_table(all_rows)

    def filter_tableBySearch(event=None):
        query = searchbar_entry.get().strip().lower()
        if not query:
            fill_table(all_rows)
            return
        filtered_data = [row for row in all_rows if any(query in str(cell).lower() for cell in row)]
        fill_table(filtered_data)

    def delete_selected_transactions():
        selected_items = tree.selection()
        if not selected_items:
            CTkMessagebox(title="Nothing selected", message="Please select at least one transaction to delete.", icon="info")
            return

        ids_to_delete = [int(tree.item(item, "values")[0]) for item in selected_items]

        confirmation = CTkMessagebox(title="Confirm delete", message=f"Delete {len(ids_to_delete)} selected transaction(s)?", icon="warning", option_1="Cancel", option_2="Delete").get()
        if confirmation != "Delete":
            return

        user_id = get_user_id(current_user)
        delete_transactions_by_id(user_id, ids_to_delete)

        fresh_rows = view_all_transactions(user_id)
        fill_table(fresh_rows)

    delete_button = ctk.CTkButton(searchbar_frame, text="Delete", font=ctk.CTkFont(size=12), fg_color="red", width=35, command=delete_selected_transactions)
    delete_button.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    searchbar_label = ctk.CTkLabel(searchbar_frame, text="Search Bar:", font=ctk.CTkFont(size=12))
    searchbar_label.grid(row=0, column=1, padx=2, pady=5, sticky="w")

    searchbar_entry = ctk.CTkEntry(searchbar_frame, width=150)
    searchbar_entry.grid(row=0, column=2, padx=2, pady=5, sticky="ew")

    searchbar_frame.grid_columnconfigure(1, weight=1)

    searchbar_entry.bind("<KeyRelease>", filter_tableBySearch)

def show_delete_data():
    clear_content()
    ctk.CTkLabel(content_frame, text="Delete all data", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))
    ctk.CTkLabel(content_frame, text="Are you sure you want to delete all data? If you are, type 'DELETE ALL DATA' in the text box and hit the delete button:", font=ctk.CTkFont(size=12)).pack()
    delete_data_entry = ctk.CTkEntry(content_frame)
    delete_data_entry.pack()

    def delete_data():
        data_deletion = delete_data_entry.get()
        user_id = get_user_id(current_user)
        if data_deletion == str("DELETE ALL DATA"):
            clear_all_transactions(user_id)
            success = ctk.CTkLabel(content_frame, text="All data was deleted successfully!", text_color="red", font=ctk.CTkFont(family='arial', size=12))
            success.pack()
            success.after(5000, success.destroy)
        else:
            error = ctk.CTkLabel(content_frame, text="Invalid confirmation! Data not deleted!", text_color="red", font=ctk.CTkFont(family='arial', size=12))
            error.pack()
            error.after(5000, error.destroy)

    ctk.CTkButton(content_frame, text="Delete", command=delete_data, fg_color="red").pack(pady=40)

def chart_selection_screen():
    clear_content()

    ctk.CTkLabel(content_frame, text="Charts", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
    ctk.CTkLabel(content_frame, text="Please input a year and choose a chart to generate.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

    chart_selection_frame = ctk.CTkFrame(content_frame, corner_radius=0)
    chart_selection_frame.pack(fill="both", expand=True, padx=20, pady=20)

    description_labels_frame = ctk.CTkFrame(chart_selection_frame)
    description_labels_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

    option_frame = ctk.CTkFrame(chart_selection_frame)
    option_frame.grid(row=1, column=0, sticky="nsew", padx=350, pady=(10, 20))

    year_var = ctk.StringVar()
    chart_var = ctk.StringVar(value="pie")

    ctk.CTkLabel(option_frame, text="You can leave the year entry empty if you want to view everything at once.", font=ctk.CTkFont(size=12)).pack(pady=(5, 0))

    ctk.CTkLabel(option_frame, text="Enter year:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))
    year_entry = ctk.CTkEntry(option_frame, textvariable=year_var)
    year_entry.pack(pady=5)

    ctk.CTkLabel(option_frame, text="Select Chart Type:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0))

    chart_label = ctk.CTkLabel(description_labels_frame, text="", wraplength=600, font=ctk.CTkFont(size=16, weight="bold"))
    chart_label.pack(pady=(10, 0))
    description_label = ctk.CTkLabel(description_labels_frame, text="", wraplength=600, font=ctk.CTkFont(size=12))
    description_label.pack(pady=(0, 20))

    def update_description_and_chart_labels(selection):
        label = CHART_LABELS.get(selection, "Unknown chart")
        description = CHART_DESCRIPTIONS.get(selection, "No description available.")
        chart_label.configure(text=f"{label}")
        description_label.configure(text=f"{description}")

    chart_menu = ctk.CTkOptionMenu(
        option_frame,
        variable=chart_var,
        values=list(CHART_LABELS.keys()),
        command=update_description_and_chart_labels
    )
    chart_menu.pack()

    update_description_and_chart_labels(chart_var.get())

    chart_selection_frame.grid_rowconfigure(0, weight=0)
    chart_selection_frame.grid_rowconfigure(1, weight=10)
    chart_selection_frame.grid_columnconfigure(0, weight=1)

    def proceed():
        year = year_var.get()
        chart_type = chart_var.get()
        show_chart(chart_type, year)

    ctk.CTkButton(option_frame, text="Generate Chart", command=proceed).pack(pady=20)

def show_chart(chart_type, year=None):
    clear_content()
    type_filter_var = ctk.StringVar(value="all")

    def draw_chart():
        for widget in content_frame.winfo_children():
            if getattr(widget, "is_chart_widget", False):
                widget.destroy()

        user_id = get_user_id(current_user)
        db_table = view_all_transactions(user_id)

        if year:
            try:
                db_table = [row for row in db_table if datetime.datetime.strptime(row[1], "%d-%m-%Y").year == int(year)]
            except ValueError:
                pass

        totals_for_category = {}
        category_types = {}
        
        for row in db_table:
            category = row[2]
            description = row[3]
            amount = row[4]
            transaction_type = row[5]
            key = (category, description)
            
            if key not in totals_for_category:
                totals_for_category[key] = 0
                category_types[key] = {'income': 0, 'expense': 0}
            
            totals_for_category[key] += amount
            category_types[key][transaction_type] += abs(amount)

        category_primary_type = {}
        for key, type_amounts in category_types.items():
            if type_amounts['income'] > type_amounts['expense']:
                category_primary_type[key] = 'income'
            else:
                category_primary_type[key] = 'expense'

        labels = list(f"{cat}: {desc}" for (cat, desc) in totals_for_category.keys())
        values = list(totals_for_category.values())

        if not labels:
            label = ctk.CTkLabel(content_frame, text="No data to display.")
            label.is_chart_widget = True
            label.pack()
            return

        chart_frame = ctk.CTkFrame(content_frame)
        chart_frame.is_chart_widget = True
        chart_frame.pack(expand=True, fill="both", padx=10, pady=10)

        chart_left_frame = ctk.CTkFrame(chart_frame)
        chart_left_frame.grid(row=0, column=0, sticky="nsew")

        legend_frame = ctk.CTkFrame(chart_frame, corner_radius=0)
        legend_frame.grid(row=0, column=1, sticky="nsew")

        legend_title = ctk.CTkLabel(legend_frame, text="Category Breakdown", font=ctk.CTkFont(size=16, weight="bold"))
        legend_title.pack(pady=(0, 5))

        legend_scroll = ctk.CTkScrollableFrame(legend_frame)
        legend_scroll.pack(fill="both", expand=True, padx=(10, 0), pady=(5, 0))

        total_amount = sum(values)

        # Category items to legend
        for i, (label, value) in enumerate(zip(labels, values)):
            percentage = (value / total_amount * 100) if total_amount > 0 else 0
            
            category_key = list(totals_for_category.keys())[i]
            primary_type = category_primary_type[category_key]

            if primary_type == 'expense' and value > 0:
                amount_text = f"-€{value:,.2f} ({percentage:.1f}%)"
            else:
                amount_text = f"€{value:,.2f} ({percentage:.1f}%)"
            
            category_frame = ctk.CTkFrame(legend_scroll)
            category_frame.pack(fill="x", pady=2, padx=5)
            
            category_label = ctk.CTkLabel(category_frame, text=label, font=ctk.CTkFont(size=12, weight="bold"))
            category_label.pack(anchor="w", padx=5, pady=(5, 0))
            
            amount_label = ctk.CTkLabel(category_frame, text=amount_text, font=ctk.CTkFont(size=11))
            amount_label.pack(anchor="w", padx=5, pady=(0, 5))

        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        def format_amount(pct, allvalues):
            absolute = int(np.round(pct/100.*np.sum(allvalues)))
            return f"{pct:.1f}%\n(€{absolute:,})"
        
        if chart_type == 'pie':

            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct=lambda pct: format_amount(pct, values), 
                                             textprops=dict(color="w", size=9, weight="bold"))
            
            plt.setp(autotexts, size=9, weight="bold")

        elif chart_type == 'bar':
            ax.bar(labels, values, color="skyblue")
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Category")
            ax.set_ylabel("Total Amount (€)")
            ax.set_title("Total Amount by Category")
            ax.tick_params(axis="x", rotation=45)
            
            # Value labels for bars
            for i, v in enumerate(values):
                ax.text(i, v + max(values) * 0.01, f'€{v:,.0f}', ha='center', va='bottom')

        elif chart_type == 'donut':
            wedges, texts = ax.pie(values, wedgeprops=dict(width=0.5), startangle=-40)

            bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
            kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

            for i, p in enumerate(wedges):
                angle = (p.theta2 - p.theta1)/2. + p.theta1
                y = np.sin(np.deg2rad(angle))
                x = np.cos(np.deg2rad(angle))
                horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
                connectionstyle = f"angle,angleA=0,angleB={angle}"
                kw["arrowprops"].update({"connectionstyle": connectionstyle})
                ax.annotate(labels[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.2*y),
                            horizontalalignment=horizontalalignment, **kw)

        elif chart_type == "horizontal bar":
            top_expenses = {}
            for row in db_table:
                category = row[2]
                description = row[3]
                amount = row[4]
                transaction_type = row[5]

                if transaction_type == 'expense':
                    key = f"{category}: {description}"
                    if key not in top_expenses:
                        top_expenses[key] = 0
                    top_expenses[key] += amount

            sorted_expenses = sorted(top_expenses.items(), key=lambda x: x[1], reverse=True)[:5]

            descriptions = [item[0] for item in sorted_expenses]
            expense_values = [abs(item[1]) for item in sorted_expenses]

            y = np.arange(len(descriptions))
            width=0.4

            bars = ax.barh(y, expense_values, width, align='center')
            ax.grid(True, alpha=0.3)
            ax.set_yticks(y)
            ax.set_yticklabels(descriptions, fontsize=8)
            ax.invert_yaxis()
            ax.set_xlabel("Expense amount (€)")
            ax.set_title("Top 5 Expenses by Category & Description")

            for i, (bar, value) in enumerate(zip(bars, expense_values)):
                ax.text(bar.get_width() + max(expense_values) * 0.01, bar.get_y() + bar.get_height()/2, f'€{value:,.0f}', va='center', fontsize=8)

        elif chart_type == "surplus deficit":
            monthly_data = {}
            sorted_rows = sorted(db_table, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))

            for row in sorted_rows:
                date_str = row[1]
                amount = row[4]
                transaction_type = row[5]
                
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    month_key = f"{date_obj.strftime('%b %Y')}"
                except ValueError:
                    continue
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'income': 0, 'expense': 0}
                
                if transaction_type == 'income':
                    monthly_data[month_key]['income'] += amount
                elif transaction_type == 'expense':
                    monthly_data[month_key]['expense'] += abs(amount)
            
            months = []
            surpluses = []
            colors = []
            
            for month, data in monthly_data.items():
                months.append(month)
                surplus = data['income'] - data['expense']
                surpluses.append(surplus)
                colors.append('green' if surplus >= 0 else 'red')
            
            if not months:
                label = ctk.CTkLabel(content_frame, text="No data to display.")
                label.is_chart_widget = True
                label.pack()
                return

            bars = ax.bar(months, surpluses, color=colors, alpha=0.7)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Month")
            ax.set_ylabel("Surplus/Deficit (€)")
            ax.set_title("Monthly Surplus/Deficit Trends")
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.tick_params(axis='x', rotation=45)

            # Value labels for bars
            for bar, value in zip(bars, surpluses):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + (max(surpluses) * 0.01 if height >= 0 else -abs(min(surpluses)) * 0.01),
                       f'€{value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor='green', alpha=0.7, label='Surplus'),
                             Patch(facecolor='red', alpha=0.7, label='Deficit')]
            ax.legend(handles=legend_elements, loc='upper right')

        elif chart_type == 'savings':
            savings_data = {}
            cumulative_savings = 0
            
            sorted_rows = sorted(db_table, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))
            
            for row in sorted_rows:
                date_str = row[1]
                amount = row[4]
                transaction_type = row[5]
                
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    date_key = date_obj.strftime("%d-%m-%Y")
                except ValueError:
                    continue

                if transaction_type == 'income':
                    cumulative_savings += amount
                elif transaction_type == 'expense':
                    cumulative_savings -= abs(amount)
                
                savings_data[date_key] = cumulative_savings
            
            if not savings_data:
                label = ctk.CTkLabel(content_frame, text="No data to display.")
                label.is_chart_widget = True
                label.pack()
                return
            
            dates = list(savings_data.keys())
            savings_values = list(savings_data.values())
            date_objects = [datetime.datetime.strptime(date, "%d-%m-%Y") for date in dates]

            MAX_POINTS = 200 # Change this value to affect the date intervals in the savings chart. Greater value = bigger intervals (bigger date gaps) -> Works better with larger transaction histories.
            if len(date_objects) > MAX_POINTS:
                month_last = {}
                for date, value in zip(date_objects, savings_values):
                    key = date.strftime("%Y-%m")
                    if key not in month_last or date > month_last[key][0]:
                        month_last[key] = (date, value)

                date_objects = [value[0] for value in month_last.values()]
                savings_values = [value[1] for value in month_last.values()]
                dates = [date.strftime("%d-%m-%Y") for date in date_objects]
                sorted_pairs = sorted(zip(date_objects, savings_values))
                date_objects, savings_values = zip(*sorted_pairs)
            
            ax.plot(date_objects, savings_values, marker='o', linewidth=2, markersize=4, color='green')
            ax.set_xlabel("Date")
            ax.set_ylabel("Cumulative Savings (€)")
            ax.set_title("Savings Progress Over Time")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)

            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d-%m-%Y'))
            ax.xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=max(1, len(dates)//10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Value labels for key points
            ANNOTATION_LIMIT = 6 # Edit this to affect the amount of markers on the chart.
            for i, (date, value) in enumerate(zip(date_objects, savings_values)):
                if i == 0 or i == len(savings_values) - 1 or value == max(savings_values) or value == min(savings_values) or i % (len(savings_values) // ANNOTATION_LIMIT) == 0:
                    ax.annotate(f'€{value:,.0f}', xy=(date, value), xytext=(10, 10), textcoords='offset points', fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8), arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        elif chart_type == 'bar by date_amount':
            date_data = {}

            sorted_rows = sorted(db_table, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))

            for row in sorted_rows:
                date_str = row[1]
                amount = row[4]
                transaction_type = row[5]

                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    month_key = date_obj.strftime("%m-%Y")
                except ValueError:
                    continue

                if month_key not in date_data:
                    date_data[month_key] = {'income': 0, 'expense': 0}
                date_data[month_key][transaction_type] += amount

            dates = list(date_data.keys())
            income_values = [date_data[date]['income'] for date in dates]
            expense_values = [abs(date_data[date]['expense']) for date in dates]

            x = np.arange(len(dates))
            width = 0.4

            bars_income = ax.bar(x, income_values, width, label="Income", color="green", alpha=0.7)
            bars_expense = ax.bar(x, [-exp for exp in expense_values], width, label="Expense", color="red", alpha=0.7)

            ax.set_xlabel("Date")
            ax.set_ylabel("Amount (€)")
            ax.set_title("Income vs. Expense by Month")
            ax.set_xticks(x)
            display_labels = [datetime.datetime.strptime(date, "%m-%Y").strftime("%b %Y") for date in dates]
            ax.set_xticklabels(display_labels, rotation=45, ha='right')
            ax.legend(loc="upper right")
            ax.grid(True, alpha=0.3)

            # Value labels for bars
            for i, (income, expense) in enumerate(zip(income_values, expense_values)):
                if income > 0:
                    ax.text(i, income + max(income_values) * 0.01, f'€{income:,.0f}', ha='center', va='bottom', fontsize=8)
                if expense > 0:
                    ax.text(i, -expense - max(expense_values) * 0.01, f'€{expense:,.0f}', ha='center', va='bottom', fontsize=8)

        elif chart_type == 'monthly category split':
            expense_rows = [row for row in db_table if row[5] == 'expense']
            month_catdesc_expense = {}
            for row in expense_rows:
                date_str = row[1]
                category = row[2]
                description = row[3]
                amount = abs(row[4])

                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    month_key = date_obj.strftime("%b %Y")
                except ValueError:
                    continue
                key = (category, description)
                if month_key not in month_catdesc_expense:
                    month_catdesc_expense[month_key] = {}
                if key not in month_catdesc_expense[month_key]:
                    month_catdesc_expense[month_key][key] = 0
                month_catdesc_expense[month_key][key] += amount

            all_months = sorted(month_catdesc_expense.keys(), key=lambda x: datetime.datetime.strptime(x, "%b %Y"))
            all_catdesc = set()
            for v in month_catdesc_expense.values():
                all_catdesc.update(v.keys())
            all_catdesc = sorted(list(all_catdesc))
            data = {catdesc: [month_catdesc_expense.get(month, {}).get(catdesc, 0) for month in all_months] for catdesc in all_catdesc}
            bottom = np.zeros(len(all_months))
            colors = plt.cm.tab20(np.linspace(0, 1, len(all_catdesc)))

            for i, catdesc in enumerate(all_catdesc):
                values = data[catdesc]
                ax.bar(all_months, values, bottom=bottom, label=f"{catdesc[0]}: {catdesc[1]}", color=colors[i % len(colors)])
                bottom += np.array(values)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("Month")
            ax.set_ylabel("Expense Amount (€)")
            ax.set_title("Monthly Expenses by Category & Description")
            ax.tick_params(axis="x", rotation=45)
            ax.legend(loc="best", fontsize=9, bbox_to_anchor=(0.98, 1), borderaxespad=0.)

        canvas = FigureCanvasTkAgg(fig, master=chart_left_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(expand=True, fill="both")

        chart_frame.grid_columnconfigure(0, weight=180)
        chart_frame.grid_columnconfigure(1, weight=0)
        chart_frame.grid_rowconfigure(0, weight=1)

    labels = CHART_LABELS.get(chart_type, "Chart not available.")
    description = CHART_DESCRIPTIONS.get(chart_type, "No description available for this chart.")
    ctk.CTkLabel(content_frame, text=labels, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
    ctk.CTkLabel(content_frame, text=description, wraplength=600, justify="left").pack(pady=(0, 20))

    ctk.CTkLabel(content_frame, text="Show: ").pack(anchor=ctk.CENTER, side=ctk.TOP)
    ctk.CTkOptionMenu(
        content_frame,
        variable=type_filter_var,
        values=["all", "income", "expense"],
        command=lambda _: draw_chart()
    ).pack(anchor=ctk.CENTER, side=ctk.TOP)

    draw_chart()

max_past_n_months = 12 # Limit the amount of actual expense points shown in the graph so that the graph doesn't overfill.

def draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, parent_frame):
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        actuals = np.array(actuals, dtype=float)
        if len(months_labels) > max_past_n_months:
            months_labels = months_labels[-max_past_n_months:]
            actuals = actuals[-max_past_n_months:]

        predicted_expense = np.array([predicted_expense] if np.isscalar(predicted_expense) else predicted_expense, dtype=float).flatten()
        next_month = datetime.datetime.strptime(months_labels[-1], "%b %Y")
        future_labels = []
        for i in range(len(predicted_expense)):
            future_month = (next_month + datetime.timedelta(days=31 * (i+1))).replace(day=1)
            future_labels.append(future_month.strftime("%b %Y"))

        ax.plot(months_labels, actuals, marker='o', label="Actual expenses", color="blue")
        ax.plot([months_labels[-1]] + future_labels, [actuals[-1]] + list(predicted_expense), marker='o', linestyle="--", color="orange", label="Predicted expenses")
        ax.scatter(future_labels, predicted_expense, color="red", zorder=5)

        last_y = None
        texts = []
        for label, pred in zip(future_labels, predicted_expense):
            y_offset = 10
            if last_y is not None and abs(pred - last_y) < 100:
                y_offset += 50
            texts.append(
                ax.annotate(f"Predicted: €{pred:.2f}", xy=(label, pred), xytext=(0, y_offset), textcoords="offset points", ha="center", color="red", arrowprops=dict(arrowstyle="->", color="gray"))
            )
            last_y = pred

        ax.set_xlabel("Month")
        ax.set_ylabel("Expenses (€)")
        ax.set_title("Monthly expenses & prediction")
        ax.set_yticks(np.arange(min(actuals), max(actuals) + max(predicted_expense) + 500, 500))
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(expand=True, fill="both", padx=10, pady=10)
        widget.is_chart_widget=True

def show_prediction(prediction_type):
    clear_content()
    ctk.CTkLabel(content_frame, text="Prediction models", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

    prediction_frame = ctk.CTkFrame(content_frame, corner_radius=0)
    prediction_frame.pack(fill="both", expand=True, padx=10, pady=5)

    ctk.CTkLabel(prediction_frame, text="Note that depending on the chosen model and the amount of data, the time to make the predictions can take some time! Please wait until the graph appears.",
                 font=ctk.CTkFont(size=12), wraplength=600, justify="left").pack(pady=(10, 10))

    description = PREDICTION_MODEL_DESCRIPTIONS.get(prediction_type, "No description available for this model.")
    ctk.CTkLabel(prediction_frame, text=description, font=ctk.CTkFont(size=18), wraplength=600, justify="left").pack(pady=(10, 20))

    ctk.CTkLabel(prediction_frame, text="The number of past months to show:", font=ctk.CTkFont(size=12)).pack(pady=(70, 0))
    past_month_entry = ctk.CTkEntry(prediction_frame)
    past_month_entry.pack()
    ctk.CTkLabel(prediction_frame, text="Leaving this empty will default to the past 12 months. Does not affect the predictions. Use to prevent the graph from overfilling if there are years of transaction data that it would then try to fit in.",
                 wraplength=600, font=ctk.CTkFont(size=12)).pack(pady=5)

    ctk.CTkLabel(prediction_frame, text="Enter the amount of months to predict:", font=ctk.CTkFont(size=12)).pack(pady=(30, 0))
    month_entry = ctk.CTkEntry(prediction_frame)
    month_entry.pack()

    def clear_prediction_frame():
        for widget in prediction_frame.winfo_children():
            widget.destroy()

    def on_predict():
        global max_past_n_months

        try:
            n_months = int(month_entry.get())
            if n_months < 1:
                raise ValueError
        except ValueError:
            error = ctk.CTkLabel(prediction_frame, text="Please enter a valid positive integer.", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        past_n_months = past_month_entry.get()

        if past_n_months == "":
            past_n_months = max_past_n_months
        else:
            try:
                past_n_months = int(past_n_months)
                max_past_n_months = past_n_months
            except ValueError:
                error = ctk.CTkLabel(prediction_frame, text="Please enter a valid positive integer.", text_color="red")
                error.pack()
                error.after(2000, error.destroy)
                return

        for widget in content_frame.winfo_children():
            if hasattr(widget, "is_chart_widget") and widget.is_chart_widget:
                widget.destroy()

        user_id = get_user_id(current_user)
        if user_id is None:
            error = ctk.CTkLabel(content_frame, text="User not found. Please log in again.", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        def run_ml():
            if prediction_type == 'linear':
                predicted_expense, months, actuals = linear_model(n_future_months=n_months, user_id=user_id)
            elif prediction_type == 'polynomial':
                predicted_expense, months, actuals = polynomial_model(n_future_months=n_months, user_id=user_id)
            elif prediction_type == 'sarimax':
                predicted_expense, months, actuals = sarimax_model(n_future_months=n_months, user_id=user_id)
            elif prediction_type == 'randomforest':
                predicted_expense, months, actuals = randomforest_model(n_future_months=n_months, user_id=user_id)
            elif prediction_type == 'ensemble':
                predicted_expense, months, actuals = ensemble_model(n_future_months=n_months, user_id=user_id)
            elif prediction_type == 'xgboost':
                predicted_expense, months, actuals = xgboost_model(n_future_months=n_months, user_id=user_id)
            else:
                return

            months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]
            next_month = (datetime.datetime.strptime(months[-1], "%Y-%m") + datetime.timedelta(days=31)).replace(day=1)
            next_month_label = next_month.strftime("%b %Y")

            clear_prediction_frame()
            app.after(0, lambda: draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, prediction_frame))

        threading.Thread(target=run_ml).start()

    ctk.CTkButton(prediction_frame, text="Predict", command=on_predict).pack(pady=10)

ctk.CTkButton(button_frame, text="Home", command=show_home_screen).pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Show transaction history", command=show_all_transactions_table).pack(padx=15, pady=12)
charts_btn = ctk.CTkButton(button_frame, text="Charts", command=chart_selection_screen).pack(padx=15, pady=12)
predictions_btn = ctk.CTkButton(button_frame, text="Monthly expense predictions", command=toggle_prediction_model_buttons)
predictions_btn.pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Delete all transaction data", command=show_delete_data).pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Delete Account", command=show_delete_user).pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Logout", command=lambda: [clear_session(), login_frame.pack(fill=ctk.BOTH, expand=True), content_frame.pack_forget(), button_frame.pack_forget(), show_login_screen()]).pack(padx=15, pady=12)

def require_login(func):
    def wrapper(*args, **kwargs):
        if current_user is None:
            error = ctk.CTkLabel(content_frame, text="Please log in to access this feature!", text_color="red")
            error.pack()
            error.after(2000, lambda: [error.destroy(), show_login_screen()])
            return
        return func(*args, **kwargs)
    return wrapper

show_all_transactions_table = require_login(show_all_transactions_table)
show_delete_data = require_login(show_delete_data)
show_chart = require_login(show_chart)
show_prediction = require_login(show_prediction)

if __name__ == "__main__":
    init_db()
    show_login_screen()
    app.mainloop()