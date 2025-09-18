from .baseChart import Chart
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class donutChart(Chart):
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

        wedges, texts = ax.pie(values, wedgeprops=dict(width=0.5), startangle=-40)

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(
            arrowprops=dict(arrowstyle="-", lw=0.5),
            bbox=bbox_props,
            zorder=0,
            va="center",
            color="black",
            fontsize=8
        )

        for i, p in enumerate(wedges):
            angle = (p.theta2 - p.theta1)/2. + p.theta1
            y = np.sin(np.deg2rad(angle))
            x = np.cos(np.deg2rad(angle))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={angle}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})

            radius = 1.1 + 0.1 * (i % 3)
            xytext = (1.3 * np.sign(x), radius * y * 1.2)
            ax.annotate(
                labels[i],
                xy=(x, y),
                xytext=xytext,
                horizontalalignment=horizontalalignment,
                **kw
            )

        canvas = FigureCanvasTkAgg(fig, master=chartFrameLeft)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")