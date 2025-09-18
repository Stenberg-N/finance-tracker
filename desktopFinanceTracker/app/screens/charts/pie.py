from .baseChart import Chart
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt

class pieChart(Chart):
    def draw(self, chartFrame, dbTable, labels, values):
        if not labels:
            label = ctk.CTkLabel(chartFrame, text="No data to display.")
            label.pack()
            return
        
        chartFrameLeft = ctk.CTkFrame(chartFrame)
        chartFrameLeft.grid(row=0, column=0, sticky="nsew")

        plt.style.use('dark_background')
        fig = Figure(figsize=(8, 6), dpi=100, facecolor="#101010")
        ax = fig.add_subplot(111)

        def formatAmount(pct, allValues):
            absolute = int(np.round(pct/100.*np.sum(allValues)))
            return f"{pct:.1f}%\n(€{absolute:,})"
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct=lambda pct: formatAmount(pct, values), textprops=dict(color="w", size=9, weight="bold"))
        plt.setp(autotexts, size=9, weight="bold")

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")