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
import matplotlib.pyplot as plt
import numpy as np
from ml import linear_model, polynomial_model, robust_linear_model, ridge_model, arima_model, randomforest_model, ensemble_model

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

PREDICTION_MODEL_DESCRIPTIONS = {
    'linear': "Linear Regression: Best for data with a linear trend.",
    'polynomial': "Polynomial Regression: Captures non-linear trends. Useful if your expenses have curves or seasonal effects.",
    'robust linear': "Robust Linear Regression: Like linear regression, but less sensitive to outliers.",
    'ridge': "Ridge Regression: Linear model with regularization. Helps prevent overfitting if or when you have many features.",
    'arima': "ARIMA: Time series model. Good for data with trends and seasonality.",
    'randomforest': "Random Forest: Combines many decision trees to make better predictions, even with complex or unusual data.",
    'ensemble': "Ensemble: Combines multiple models for improved accuracy and robustness.",
}

button_frame = ctk.CTkFrame(app)
button_frame.pack(side=ctk.LEFT, fill=ctk.Y, anchor=ctk.N)

pie_chart_btn = ctk.CTkButton(button_frame, text="Pie chart", command=lambda: show_chart('pie'))
bar_plot_btn = ctk.CTkButton(button_frame, text="Bar plot", command=lambda: show_chart('bar'))
donut_chart_btn = ctk.CTkButton(button_frame, text="Donut chart", command=lambda: show_chart('donut'))
stacked_bar_btn = ctk.CTkButton(button_frame, text="Stacked Bar chart", command=lambda: show_chart('stacked bar'))
horizontal_bar_btn = ctk.CTkButton(button_frame, text="Top 5 Expenses chart", command=lambda: show_chart('horizontal bar'))
surplus_deficit_btn = ctk.CTkButton(button_frame, text="Surplus/Deficit chart", command=lambda: show_chart('surplus deficit'))
savings_progress_btn = ctk.CTkButton(button_frame, text="Saving chart", command=lambda: show_chart('savings'))
pie_chart_btn.pack_forget()
bar_plot_btn.pack_forget()
donut_chart_btn.pack_forget()
stacked_bar_btn.pack_forget()
horizontal_bar_btn.pack_forget()
surplus_deficit_btn.pack_forget()
savings_progress_btn.pack_forget()

linear_regression_btn = ctk.CTkButton(button_frame, text="Linear", command=lambda: show_prediction('linear'))
poly_regression_btn = ctk.CTkButton(button_frame, text="Polynomial", command=lambda: show_prediction('polynomial'))
robust_linear_btn = ctk.CTkButton(button_frame, text="Robust Linear", command=lambda: show_prediction('robust linear'))
ridge_btn = ctk.CTkButton(button_frame, text="Ridge", command=lambda: show_prediction('ridge'))
arima_btn = ctk.CTkButton(button_frame, text="ARIMA", command=lambda: show_prediction('arima'))
randomforest_btn = ctk.CTkButton(button_frame, text="RandomForest", command=lambda: show_prediction('randomforest'))
ensemble_btn = ctk.CTkButton(button_frame, text="Ensemble", command=lambda: show_prediction('ensemble'))
linear_regression_btn.pack_forget()
poly_regression_btn.pack_forget()
robust_linear_btn.pack_forget()
ridge_btn.pack_forget()
arima_btn.pack_forget()
randomforest_btn.pack_forget()
ensemble_btn.pack_forget()

by_month_btn = ctk.CTkButton(button_frame, text="Month", command=lambda: show_transactions_by('month'))
by_week_btn = ctk.CTkButton(button_frame, text="Week", command=lambda: show_transactions_by('week'))
by_month_btn.pack_forget()
by_week_btn.pack_forget()

content_frame = ctk.CTkFrame(app)
content_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def toggle_prediction_model_buttons():
    if linear_regression_btn.winfo_ismapped():
        linear_regression_btn.pack_forget()
        poly_regression_btn.pack_forget()
        robust_linear_btn.pack_forget()
        ridge_btn.pack_forget()
        arima_btn.pack_forget()
        randomforest_btn.pack_forget()
        ensemble_btn.pack_forget()
    else:
        linear_regression_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        poly_regression_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        robust_linear_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        ridge_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        arima_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        randomforest_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)
        ensemble_btn.pack(after=predictions_btn, pady=2, anchor=ctk.E)

def toggle_chart_buttons():
    if pie_chart_btn.winfo_ismapped():
        pie_chart_btn.pack_forget()
        bar_plot_btn.pack_forget()
        donut_chart_btn.pack_forget()
        stacked_bar_btn.pack_forget()
        horizontal_bar_btn.pack_forget()
        surplus_deficit_btn.pack_forget()
        savings_progress_btn.pack_forget()
    else:
        pie_chart_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        bar_plot_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        donut_chart_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        stacked_bar_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        horizontal_bar_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        surplus_deficit_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)
        savings_progress_btn.pack(after=charts_btn, pady=2, anchor=ctk.E)


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

def all_transactions_treeview():
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
    return tree

def show_all_transactions_table():
    clear_content()
    tree = all_transactions_treeview()

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

            tree = all_transactions_treeview()

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

            tree = all_transactions_treeview()

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
        category_types = {}
        
        for row in rows:
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
        chart_left_frame.pack(side=ctk.LEFT, fill="both", expand=True, padx=(0, 10))

        legend_frame = ctk.CTkFrame(chart_frame)
        legend_frame.pack(side=ctk.RIGHT, fill="both", padx=(10, 0))

        legend_title = ctk.CTkLabel(legend_frame, text="Category Breakdown", font=ctk.CTkFont(size=16, weight="bold"))
        legend_title.pack(pady=(10, 5))

        legend_scroll = ctk.CTkScrollableFrame(legend_frame, width=300)
        legend_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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
                
        elif chart_type == 'stacked bar':
            category_data = {}
            for row in rows:
                category = row[2]
                amount = row[4]
                transaction_type = row[5]

                if category not in category_data:
                    category_data[category] = {'income': 0, 'expense': 0}

                category_data[category][transaction_type] += amount

            categories = list(category_data.keys())
            income_values = [category_data[cat]['income'] for cat in categories]
            expense_values = [abs(category_data[cat]['expense']) for cat in categories]
        
            x = np.arange(len(categories))
            width = 0.4

            bars_income = ax.bar(x, income_values, width, label="Income", color="green", alpha=0.7)
            bars_expense = ax.bar(x, [-exp for exp in expense_values], width, label="Expense", color="red", alpha=0.7)

            ax.set_xlabel("Category")
            ax.set_ylabel("Amount (€)")
            ax.set_title("Income vs. Expense by category")
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend(loc="upper right")
            ax.grid(True, alpha=0.3)

            # Value labels for bars
            for i, (income, expense) in enumerate(zip(income_values, expense_values)):
                if income > 0:
                    ax.text(i, income + max(income_values) * 0.01, f'€{income:,.0f}', ha='center', va='bottom', fontsize=8)
                if expense > 0:
                    ax.text(i, -expense - max(expense_values) * 0.01, f'€{expense:,.0f}', ha='center', va='bottom', fontsize=8)

        elif chart_type == "horizontal bar":
            top_expenses = {}
            for row in rows:
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
            ax.set_yticks(y)
            ax.set_yticklabels(descriptions, fontsize=8)
            ax.invert_yaxis()
            ax.set_xlabel("Expense amount (€)")
            ax.set_title("Top 5 Expenses by Category & Description")

            for i, (bar, value) in enumerate(zip(bars, expense_values)):
                ax.text(bar.get_width() + max(expense_values) * 0.01, bar.get_y() + bar.get_height()/2, f'€{value:,.0f}', va='center', fontsize=8)

        elif chart_type == "surplus deficit":
            monthly_data = {}
            for row in rows:
                date_str = row[1]
                amount = row[4]
                transaction_type = row[5]
                
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                    month_key = f"{date_obj.strftime('%B %Y')}"
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
            
            sorted_rows = sorted(rows, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))
            
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
            for i, (date, value) in enumerate(zip(date_objects, savings_values)):
                if i == 0 or i == len(savings_values) - 1 or value == max(savings_values) or value == min(savings_values):
                    ax.annotate(f'€{value:,.0f}', xy=(date, value), xytext=(10, 10), textcoords='offset points', fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8), arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        canvas = FigureCanvasTkAgg(fig, master=chart_left_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(expand=True, fill="both")

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

def draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, parent_frame):
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(months_labels, actuals, marker='o', label="Actual expenses", color="blue")
        ax.plot(months_labels + [next_month_label], list(actuals) + [predicted_expense], marker='o', linestyle="--", color="orange", label="Predicted next month")
        ax.scatter([next_month_label], [predicted_expense], color="red", zorder=5)
        ax.set_xlabel("Month")
        ax.set_ylabel("Expenses (€)")
        ax.set_title("Monthly expenses & next month prediction")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)
        ax.annotate(f"Predicted: €{predicted_expense:.2f}", xy=(next_month_label, predicted_expense), xytext=(0, 10), textcoords="offset points", ha="center", color="red")

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(expand=True, fill="both")

def show_prediction(prediction_type):
    clear_content()
    description = PREDICTION_MODEL_DESCRIPTIONS.get(prediction_type, "No description available for this model.")
    ctk.CTkLabel(content_frame, text=description, wraplength=600, justify="left").pack(pady=(10, 20))

    if prediction_type == 'linear':
        predicted_expense, months, actuals = linear_model()
    elif prediction_type == 'polynomial':
        predicted_expense, months, actuals = polynomial_model()
    elif prediction_type == 'robust linear':
        predicted_expense, months, actuals = robust_linear_model()
    elif prediction_type == 'ridge':
        predicted_expense, months, actuals = ridge_model()
    elif prediction_type == 'arima':
        predicted_expense, months, actuals = arima_model()
    elif prediction_type == 'randomforest':
        predicted_expense, months, actuals = randomforest_model()
    elif prediction_type == 'ensemble':
        predicted_expense, months, actuals = ensemble_model()
    else:
        return

    months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]
    next_month = (datetime.datetime.strptime(months[-1], "%Y-%m") + datetime.timedelta(days=31)).replace(day=1)
    next_month_label = next_month.strftime("%b %Y")

    draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, content_frame)

ctk.CTkButton(button_frame, text="Add transaction", command=show_add_transaction).pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Show transaction history", command=show_all_transactions_table).pack(padx=15, pady=12)
filter_by_btn = ctk.CTkButton(button_frame, text="Show by...", command=toggle_filter_by_buttons)
filter_by_btn.pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Exports", command=show_export_options).pack(padx=15, pady=12)
charts_btn = ctk.CTkButton(button_frame, text="Charts", command=toggle_chart_buttons)
charts_btn.pack(padx=15, pady=12)
predictions_btn = ctk.CTkButton(button_frame, text="Monthly expense predictions", command=toggle_prediction_model_buttons)
predictions_btn.pack(padx=15, pady=12)
ctk.CTkButton(button_frame, text="Delete all transaction data", command=show_delete_data).pack(padx=15, pady=12)

app.mainloop()