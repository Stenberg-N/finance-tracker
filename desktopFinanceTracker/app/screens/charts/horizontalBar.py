from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class top5ExpensesChart(Chart):
    def draw(self, chartFrame, dbTable, labels, values):
        if not labels:
            label = ctk.CTkLabel(chartFrame, text="No data to display.")
            label.pack()
            return

        chartFrameLeft = ctk.CTkFrame(chartFrame)
        chartFrameLeft.grid(row=0, column=0, sticky="nsew")

        plt.style.use('dark_background')
        fig = Figure(figsize=(10, 9), dpi=100, facecolor="#101010")
        ax = fig.add_subplot(111)

        topExpenses = {}
        for row in dbTable:
            category = row[2]
            description = row[3]
            amount = row[4]
            transactionType = row[5]

            if transactionType == 'expense':
                key = f"{category}: {description}"
                if key not in topExpenses:
                    topExpenses[key] = 0
                topExpenses[key] += amount

        sortedExpenses = sorted(topExpenses.items(), key=lambda x: x[1], reverse=True)[:5]

        descriptions = [item[0] for item in sortedExpenses]
        expenseValues = [abs(item[1]) for item in sortedExpenses]

        y = np.arange(len(descriptions))
        width=0.4

        bars = ax.barh(y, expenseValues, width, align='center', color="green")
        ax.grid(True, alpha=0.3)
        ax.set_yticks(y)
        ax.set_yticklabels(descriptions, fontsize=10, rotation=45)
        ax.invert_yaxis()
        ax.set_xlabel("Expense amount (€)")
        ax.set_title("Top 5 Expenses by Category & Description")

        for i, (bar, value) in enumerate(zip(bars, expenseValues)):
            ax.text(bar.get_width() + max(expenseValues) * 0.01, bar.get_y() + bar.get_height()/2, f'€{value:,.0f}', va='center', fontsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")