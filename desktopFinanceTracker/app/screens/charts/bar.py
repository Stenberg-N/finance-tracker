from .baseChart import Chart
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class barChart(Chart):
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

        ax.bar(labels, values, color="orange")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Category")
        ax.set_ylabel("Total Amount (€)")
        ax.set_title("Total Amount by Category")
        ax.tick_params(axis="x", rotation=45)

        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.01, f'€{v:,.0f}', ha='center', va='bottom')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")