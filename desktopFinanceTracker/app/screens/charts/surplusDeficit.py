from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

class surplusDeficitChart(Chart):
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

        monthly_data = {}
        sorted_rows = sorted(dbTable, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))

        for row in sorted_rows:
            date = row[1]
            amount = row[4]
            transactionType = row[5]
            
            try:
                date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
                month_key = f"{date_obj.strftime('%b %Y')}"
            except ValueError:
                continue
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': 0, 'expense': 0}
            
            if transactionType == 'income':
                monthly_data[month_key]['income'] += amount
            elif transactionType == 'expense':
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
            label = ctk.CTkLabel(chartFrame, text="No data to display.")
            label.pack()
            return

        bars = ax.bar(months, surpluses, color=colors, alpha=0.7)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Month")
        ax.set_ylabel("Surplus/Deficit (€)")
        ax.set_title("Monthly Surplus/Deficit Trends")
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.tick_params(axis='x', rotation=45)

        for bar, value in zip(bars, surpluses):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (max(surpluses) * 0.01 if height >= 0 else -abs(min(surpluses)) * 0.01),
                    f'€{value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

        legend_elements = [Patch(facecolor='green', alpha=0.7, label='Surplus'),
                            Patch(facecolor='red', alpha=0.7, label='Deficit')]
        ax.legend(handles=legend_elements, loc='upper right')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")