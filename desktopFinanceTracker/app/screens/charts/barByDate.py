from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import datetime

class barByDateChart(Chart):
    def draw(self, chartFrame, dbTable, labels, values):
        if not labels:
            label = ctk.CTkLabel(chartFrame, text="No data to display.")
            label.pack()
            return

        chartFrameLeft = ctk.CTkFrame(chartFrame)
        chartFrameLeft.grid(row=0, column=0, sticky="nsew")

        plt.style.use('dark_background')
        fig = Figure(figsize=(12, 9), dpi=100, facecolor="#101010")
        ax = fig.add_subplot(111)

        date_data = {}

        sorted_rows = sorted(dbTable, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))

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

        for i, (income, expense) in enumerate(zip(income_values, expense_values)):
            if income > 0:
                ax.text(i, income + max(income_values) * 0.01, f'€{income:,.0f}', ha='center', va='bottom', fontsize=8)
            if expense > 0:
                ax.text(i, -expense - max(expense_values) * 0.01, f'€{expense:,.0f}', ha='center', va='bottom', fontsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")