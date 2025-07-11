# Finance tracker

from database.db import init_db, insert_transaction, view_all_transactions, view_transactions_by_month, view_transactions_by_week, clear_all_transactions, type_column_exists, migrate_add_type_column
from exports import export_transactions_to_csv, export_transactions_to_excel, export_transactions_to_pdf
import os
import config
import customtkinter as ctk
import datetime
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

script_directory = os.path.dirname(os.path.abspath(__file__))
config.db_path = os.path.join(script_directory, 'database', 'finance.db')
config.exports_path = os.path.join(script_directory, 'exports')

init_db()
if not type_column_exists():
    migrate_add_type_column()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Finance Tracker")
app.geometry("1600x900")

button_frame = ctk.CTkFrame(app)
button_frame.pack(side=ctk.LEFT, fill=ctk.Y, anchor=ctk.N)

pie_chart_btn = ctk.CTkButton(button_frame, text="Pie chart", command=lambda: show_chart('pie'))
bar_plot_btn = ctk.CTkButton(button_frame, text="Bar plot", command=lambda: show_chart('bar'))
pie_chart_btn.pack_forget()
bar_plot_btn.pack_forget()

by_month_btn = ctk.CTkButton(button_frame, text="Month", command=lambda: show_transactions_by('month'))
by_week_btn = ctk.CTkButton(button_frame, text="Week", command=lambda: show_transactions_by('week'))
by_month_btn.pack_forget()
by_week_btn.pack_forget()

content_frame = ctk.CTkFrame(app)
content_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def toggle_chart_buttons():
    if pie_chart_btn.winfo_ismapped():
        pie_chart_btn.pack_forget()
        bar_plot_btn.pack_forget()
    else:
        pie_chart_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        bar_plot_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)


def toggle_filter_by_buttons():
    if by_month_btn.winfo_ismapped():
        by_month_btn.pack_forget()
        by_week_btn.pack_forget()
    else:
        by_month_btn.pack(after=filter_by_btn, pady=2, anchor=ctk.E)
        by_week_btn.pack(after=filter_by_btn, pady=2, anchor=ctk.E)

def show_add_transaction():
    clear_content()
    ctk.CTkLabel(content_frame, text="Type:").pack()
    type_var = ctk.StringVar(value="Select")
    type_option = ctk.CTkOptionMenu(content_frame, variable=type_var, values=["income", "expense"])
    type_option.pack()

    ctk.CTkLabel(content_frame, text="Date (DD-MM-YYYY):").pack()
    date_entry = ctk.CTkEntry(content_frame)
    date_entry.pack()

    ctk.CTkLabel(content_frame, text="Category:").pack()
    category_entry = ctk.CTkEntry(content_frame)
    category_entry.pack()

    ctk.CTkLabel(content_frame, text="Description:").pack()
    description_entry = ctk.CTkEntry(content_frame)
    description_entry.pack()

    ctk.CTkLabel(content_frame, text="Amount:").pack()
    amount_entry = ctk.CTkEntry(content_frame)
    amount_entry.pack()

    def submit_data():
        date = date_entry.get()
        category = category_entry.get()
        description = description_entry.get()
        amount = amount_entry.get()

        try:
            amount = float(amount)
        except ValueError:
            error = ctk.CTkLabel(content_frame, text="Invalid amount!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        try:
            datetime.datetime.strptime(date, "%d-%m-%Y")
        except ValueError:
            error = ctk.CTkLabel(content_frame, text="Invalid date format!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        type_value = type_var.get()
        if type_value == "Select":
            error = ctk.CTkLabel(content_frame, text="Please select a type!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        insert_transaction(date, category, description, amount, type_value)
        success = ctk.CTkLabel(content_frame, text="Transaction was successfully added!", text_color="green")
        success.pack()
        success.after(1000, show_add_transaction)
        
    ctk.CTkButton(content_frame, text="Add", command=submit_data).pack(pady=10)

def show_all_transactions_table():
    clear_content()
    tree = ttk.Treeview(content_frame, column=("c1", "c2", "c3", "c4", "c5", "c6"), show="headings")
    tree.column("#1", anchor=ctk.CENTER)
    tree.heading("#1", text="ID")
    tree.column("#2", anchor=ctk.CENTER)
    tree.heading("#2", text="Date")
    tree.column("#3", anchor=ctk.CENTER)
    tree.heading("#3", text="Category")
    tree.column("#4", anchor=ctk.CENTER)
    tree.heading("#4", text="Description")
    tree.column("#5", anchor=ctk.CENTER)
    tree.heading("#5", text="Amount")
    tree.column("#6", anchor=ctk.CENTER)
    tree.heading("#6", text="Type")
    tree.pack(expand=True, fill="both")

    rows = view_all_transactions()
    for row in rows:
        tree.insert("", ctk.END, values=row)

def show_transactions_by(filter_by):
    clear_content()
    if filter_by == 'month':

        clear_content()
        ctk.CTkLabel(content_frame, text="Month (MM):").pack()
        month_entry = ctk.CTkEntry(content_frame)
        month_entry.pack()
        ctk.CTkLabel(content_frame, text="Year (YYYY):").pack()
        year_entry = ctk.CTkEntry(content_frame)
        year_entry.pack()

        def fetch_and_show_month():
            try:
                month = int(month_entry.get())
                year = int(year_entry.get())
                if not (1 <= month <= 12):
                    raise ValueError
            except ValueError:
                error = ctk.CTkLabel(content_frame, text="Invalid month or year!", text_color="red")
                error.pack()
                error.after(2000, error.destroy)
                return
            
            for widget in content_frame.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    widget.destroy()

            tree = ttk.Treeview(content_frame, column=("c1", "c2", "c3", "c4", "c5", "c6"), show="headings")
            tree.column("#1", anchor=ctk.CENTER)
            tree.heading("#1", text="ID")
            tree.column("#2", anchor=ctk.CENTER)
            tree.heading("#2", text="Date")
            tree.column("#3", anchor=ctk.CENTER)
            tree.heading("#3", text="Category")
            tree.column("#4", anchor=ctk.CENTER)
            tree.heading("#4", text="Description")
            tree.column("#5", anchor=ctk.CENTER)
            tree.heading("#5", text="Amount")
            tree.column("#6", anchor=ctk.CENTER)
            tree.heading("#6", text="Type")
            tree.pack(expand=True, fill="both")

            rows = view_transactions_by_month(month, year)
            for row in rows:
                tree.insert("", ctk.END, values=row)
    
        ctk.CTkButton(content_frame, text="Show transactions", command=fetch_and_show_month).pack(pady=10)

    elif filter_by == 'week':

        clear_content()
        ctk.CTkLabel(content_frame, text="Week (WW):").pack()
        week_entry = ctk.CTkEntry(content_frame)
        week_entry.pack()
        ctk.CTkLabel(content_frame, text="Year (YYYY):").pack()
        year_entry = ctk.CTkEntry(content_frame)
        year_entry.pack()

        def fetch_and_show_week():
            try:
                week = int(week_entry.get())
                year = int(year_entry.get())
                if not (1 <= week <= 52):
                    raise ValueError
            except ValueError:
                error = ctk.CTkLabel(content_frame, text="Invalid week or year!", text_color="red")
                error.pack()
                error.after(2000, error.destroy)
                return
            
            for widget in content_frame.winfo_children():
                if isinstance(widget, ttk.Treeview):
                    widget.destroy()

            tree = ttk.Treeview(content_frame, column=("c1", "c2", "c3", "c4", "c5", "c6"), show="headings")
            tree.column("#1", anchor=ctk.CENTER)
            tree.heading("#1", text="ID")
            tree.column("#2", anchor=ctk.CENTER)
            tree.heading("#2", text="Date")
            tree.column("#3", anchor=ctk.CENTER)
            tree.heading("#3", text="Category")
            tree.column("#4", anchor=ctk.CENTER)
            tree.heading("#4", text="Description")
            tree.column("#5", anchor=ctk.CENTER)
            tree.heading("#5", text="Amount")
            tree.column("#6", anchor=ctk.CENTER)
            tree.heading("#6", text="Type")
            tree.pack(expand=True, fill="both")

            rows = view_transactions_by_week(week, year)
            for row in rows:
                tree.insert("", ctk.END, values=row)

        ctk.CTkButton(content_frame, text="Show transactions", command=fetch_and_show_week).pack(pady=10)

def show_export_options():
    clear_content()
    ctk.CTkLabel(content_frame, text="Filename:").pack()
    filename_entry = ctk.CTkEntry(content_frame)
    filename_entry.pack()

    def export_to_csv():
        filename = filename_entry.get()
        export_transactions_to_csv(filename)
        success = ctk.CTkLabel(content_frame, text="Transactions were successfully exported to CSV!", text_color="green")
        success.pack()
        success.after(3000, success.destroy)

    ctk.CTkButton(content_frame, text="CSV", command=export_to_csv).pack(pady=5)

    def export_to_excel():
        filename = filename_entry.get()
        export_transactions_to_excel(filename)
        success = ctk.CTkLabel(content_frame, text="Transactions were successfully exported to Excel!", text_color="green")
        success.pack()
        success.after(3000, success.destroy)
    
    ctk.CTkButton(content_frame, text="Excel", command=export_to_excel).pack(pady=5)

    def export_to_pdf():
        filename = filename_entry.get()
        export_transactions_to_pdf(filename)
        success = ctk.CTkLabel(content_frame, text="Transactions were successfully exported to PDF!", text_color="green")
        success.pack()
        success.after(3000, success.destroy)
    
    ctk.CTkButton(content_frame, text="PDF", command=export_to_pdf).pack(pady=5)

def show_delete_data():
    clear_content()
    ctk.CTkLabel(content_frame, text="Are you sure you want to delete all data? If you are, type 'DELETE ALL DATA' in the text box and hit the delete button:").pack()
    delete_data_entry = ctk.CTkEntry(content_frame)
    delete_data_entry.pack()

    def delete_data():
        data_deletion = delete_data_entry.get()
        if data_deletion == str("DELETE ALL DATA"):
            clear_all_transactions()
            success = ctk.CTkLabel(content_frame, text="All data was deleted successfully!", text_color="red", font=ctk.CTkFont(family='arial', size=18))
            success.pack()
            success.after(5000, success.destroy)
        else:
            error = ctk.CTkLabel(content_frame, text="Invalid confirmation! Data not deleted!", text_color="red", font=ctk.CTkFont(family='arial', size=18))
            error.pack()
            error.after(5000, error.destroy)

    ctk.CTkButton(content_frame, text="Delete", command=delete_data, fg_color="red").pack(pady=40)

def show_chart(chart_type):
    clear_content()
    type_filter_var = ctk.StringVar(value="all")

    def draw_chart():
        for widget in content_frame.winfo_children():
            if getattr(widget, "is_chart_widget", False):
                widget.destroy()

        rows = view_all_transactions()
        selected_type = type_filter_var.get()
        if selected_type != "all":
            rows = [row for row in rows if row[5] == selected_type]

        totals_for_category = {}
        for row in rows:
            category = row[2]
            description = row[3]
            amount = row[4]
            key = (category, description)
            totals_for_category[key] = totals_for_category.get(key, 0) + amount

        labels = list(f"{cat}: {desc}" for (cat, desc) in totals_for_category.keys())
        values = list(totals_for_category.values())

        if not labels:
            label = ctk.CTkLabel(content_frame, text="No data to display.").pack()
            label.is_chart_widget = True
            label.pack()
            return

        fig = Figure(figsize=(10, 7), dpi=100)
        ax = fig.add_subplot(111)
        if chart_type == 'pie':
            ax.pie(values, labels=labels, autopct='%1.1f%%')
        elif chart_type == 'bar':
            ax.bar(labels, values, color="skyblue")
            ax.set_xlabel("Category")
            ax.set_ylabel("Total Amount")
            ax.set_title("Total Amount by Category")
            ax.tick_params(axis="x", rotation=10)

        canvas = FigureCanvasTkAgg(fig, master=content_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.is_chart_widget = True
        widget.pack()

    filter_frame = ctk.CTkFrame(content_frame)
    filter_frame.pack()
    ctk.CTkLabel(filter_frame, text="Show:").pack(side=ctk.LEFT)
    ctk.CTkOptionMenu(
        filter_frame,
        variable=type_filter_var,
        values=["all", "income", "expense"],
        command=lambda _: draw_chart()
    ).pack(side=ctk.LEFT)

    draw_chart()

ctk.CTkButton(button_frame, text="Add transaction", command=show_add_transaction).pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Show transaction history", command=show_all_transactions_table).pack(padx=15, pady=12)
filter_by_btn = ctk.CTkButton(button_frame, text="Show by...", command=toggle_filter_by_buttons)
filter_by_btn.pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Exports", command=show_export_options).pack(padx=15, pady=12)
charts_btn = ctk.CTkButton(button_frame, text="Charts", command=toggle_chart_buttons)
charts_btn.pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Delete all transaction data", command=show_delete_data).pack(padx=15, pady=12)

app.mainloop()