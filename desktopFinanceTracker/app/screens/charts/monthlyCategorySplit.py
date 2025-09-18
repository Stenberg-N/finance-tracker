from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import datetime
import mplcursors

class monthlyCategorySplitChart(Chart):
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

        expense_rows = [row for row in dbTable if row[5] == 'expense']
        month_catdesc_expense = {}
        for row in expense_rows:
            date = row[1]
            category = row[2]
            description = row[3]
            amount = abs(row[4])

            try:
                date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
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

        bars = []
        for i, catdesc in enumerate(all_catdesc):
            values = data[catdesc]
            bar = ax.bar(all_months, values, bottom=bottom, label=f"{catdesc[0]}: {catdesc[1]}", color=colors[i % len(colors)])
            bars.append(bar)
            bottom += np.array(values)

        if len(bottom) > 0:
            max_y = max(bottom)
            ax.set_ylim(0, max_y * 1.05)

        cursor = mplcursors.cursor(bars, hover=True)
        @cursor.connect("add")
        def on_add(sel):
            bar = sel.artist
            index = sel.index
            try:
                height = bar[index].get_height()
                month = all_months[index]
                for i, catdesc in enumerate(all_catdesc):
                    if bar == bars[i]:
                        category, description = catdesc
                        sel.annotation.set_text(f"Month: {month}\nCategory: {category}\nDescription: {description}\nAmount: €{height:.2f}")
                        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8, edgecolor="#4c519c", linewidth=2)
                        sel.annotation.set_color("black")
                        sel.annotation.arrow_patch.set(color="#4c519c")
                        break
            except (IndexError, TypeError):
                sel.annotation.set_text("Error: could not retrieve data.")

        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Month")
        ax.set_ylabel("Expense Amount (€)")
        ax.set_title("Monthly Expenses by Category & Description")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="best", fontsize=9, bbox_to_anchor=(0.98, 1), borderaxespad=0.)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")