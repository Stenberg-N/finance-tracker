from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patheffects as pe
import matplotlib.dates as mdates
import datetime

class savingsChart(Chart):
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

        savings_data = {}
        cumulative_savings = 0
        
        sorted_rows = sorted(dbTable, key=lambda x: datetime.datetime.strptime(x[1], "%d-%m-%Y"))
        
        for row in sorted_rows:
            date = row[1]
            amount = row[4]
            transactionType = row[5]
            
            try:
                date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
                date_key = date_obj.strftime("%d-%m-%Y")
            except ValueError:
                continue

            if transactionType == 'income':
                cumulative_savings += amount
            elif transactionType == 'expense':
                cumulative_savings -= abs(amount)
            
            savings_data[date_key] = cumulative_savings
        
        if not savings_data:
            label = ctk.CTkLabel(chartFrame, text="No data to display.")
            label.pack()
            return
        
        dates = list(savings_data.keys())
        savings_values = list(savings_data.values())
        date_objects = [datetime.datetime.strptime(date, "%d-%m-%Y") for date in dates]

        MAX_POINTS = 200 # Change this value to affect the date intervals in the savings chart. Greater value = more data shown
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
        
        ax.plot(date_objects, savings_values, marker='o', linewidth=2, markersize=4, color="#00FF00")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Savings (€)")
        ax.set_title("Savings Progress Over Time")
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='#C80000', linestyle='-', alpha=0.5)

        locator = mdates.AutoDateLocator(maxticks=15)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        ANNOTATION_LIMIT = 6 # Edit this to affect the amount of markers on the chart.
        for i, (date, value) in enumerate(zip(date_objects, savings_values)):
            if i == 0 or i == len(savings_values) - 1 or value == max(savings_values) or value == min(savings_values) or i % (len(savings_values) // ANNOTATION_LIMIT) == 0:
                ax.annotate(
                    f'€{value:,.0f}',
                    xy=(date, value),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    color="#FF9100",
                    weight="bold",
                    path_effects=[pe.withStroke(linewidth=3, foreground="#000000")]
                )

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")