import customtkinter as ctk
from app.utils.chartpreparation import prepareChartData
from app.screens.charts.pie import pieChart
from app.screens.charts.bar import barChart
from app.screens.charts.donut import donutChart
from app.screens.charts.horizontalBar import top5ExpensesChart
from app.screens.charts.surplusDeficit import surplusDeficitChart
from app.screens.charts.savings import savingsChart
from app.screens.charts.barByDate import barByDateChart
from app.screens.charts.monthlyCategorySplit import monthlyCategorySplitChart

class chartsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app
        self.typeFilterVar = ctk.StringVar(value="all")
        self.chartTypeVar = ctk.StringVar(value="pie")
        self.yearVar = ctk.StringVar(value="")
        self.chartFrame = None
        self.legendFrame = None

        self.chartTypes = {
            "pie": (pieChart(), "Pie Chart", "A pie chart of all transactions."),
            "donut": (donutChart(), "Donut Chart", "A donut chart of all transactions."),
            "bar": (barChart(), "Bar Chart", "A bar chart of all transactions by category and description"),
            "horizontalBar": (top5ExpensesChart(), "Top 5 Expenses", "Horizontal bar chart for your top 5 expenses."),
            "surplusDeficit": (surplusDeficitChart(), "Surplus/Deficit Chart", "Subtracts expenses from income on a monthly basis and shows whether profit or loss was made."),
            "savings": (savingsChart(), "Savings Chart", "Displays the trend of your transactions. Also shows if you are in the negative. May act in a bizarre way if stating a year to generate a chart from. This chart is mainly for a long period, so it is suggested to leave the year empty."),
            "barByDate": (barByDateChart(), "Monthly transactions Chart", "Displays both income and expenses per month."),
            "monthlyCategorySplit": (monthlyCategorySplitChart(), "Stacked Bar Chart", "Displays monthly expenses split by category and description.")
        }

        self.chartNameVar = ctk.StringVar(value=self.getChartName("pie"))
        self.chartDescVar = ctk.StringVar(value=self.getChartDesc("pie"))

        self.chartTypeVar.trace_add("write", self.updateChartInfo)

        self.buildUI()

    def getChartName(self, chartKey):
        return self.chartTypes.get(chartKey, (None, "Unknown Chart", None))[1]
    
    def getChartDesc(self, ChartKey):
        return self.chartTypes.get(ChartKey, (None, None, "No description available"))[2]
    
    def updateChartInfo(self, *args):
        chartKey = self.chartTypeVar.get()
        self.chartNameVar.set(self.getChartName(chartKey))
        self.chartDescVar.set(self.getChartDesc(chartKey))

    def buildUI(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)

        ctk.CTkLabel(self, text="Charts", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(self, textvariable=self.chartNameVar, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(self, textvariable=self.chartDescVar, wraplength=600, justify="left").pack(pady=(0, 20))

        filterFrame = ctk.CTkFrame(self, fg_color="transparent")
        filterFrame.pack(anchor=ctk.W, padx=20, pady=5)

        ctk.CTkLabel(filterFrame, text="Show: ").pack(side="left", padx=5)
        ctk.CTkOptionMenu(filterFrame, variable=self.typeFilterVar, values=["all", "income", "expense"], corner_radius=0).pack(side="left", padx=5)

        ctk.CTkLabel(filterFrame, text="Chart Type: ").pack(side="left", padx=5)
        ctk.CTkOptionMenu(filterFrame, variable=self.chartTypeVar, values=list(self.chartTypes.keys()), corner_radius=0).pack(side="left", padx=(5))

        ctk.CTkLabel(filterFrame, text="Year: ").pack(side="left", padx=5)
        self.yearEntry = ctk.CTkEntry(filterFrame, width=100, placeholder_text="YYYY")
        self.yearEntry.pack(side="left", padx=5)

        ctk.CTkButton(filterFrame, text="Generate", command=self.drawChart, width=40, fg_color="#349c30", hover_color="#1f5f1d").pack(side="left", padx=(5, 0))

        self.chartFrame = ctk.CTkFrame(self, fg_color="#101010")
        self.chartFrame.pack(expand=True, fill="both")
        self.chartFrame.grid_columnconfigure(0, weight=180)
        self.chartFrame.grid_columnconfigure(1, weight=0)
        self.chartFrame.grid_rowconfigure(0, weight=1)

        self.legendFrame = ctk.CTkFrame(self.chartFrame, fg_color="#101010", corner_radius=0)
        self.legendFrame.grid(row=0, column=1, sticky="nsew")

    def drawChart(self):
        if not self.app.currentUser:
            return
        
        for widget in self.chartFrame.winfo_children():
            widget.destroy()

        self.legendFrame = ctk.CTkFrame(self.chartFrame, fg_color="#101010", corner_radius=0)
        self.legendFrame.grid(row=0, column=1, sticky="nsew")

        legendTitle = ctk.CTkLabel(self.legendFrame, text="Category Breakdown", font=ctk.CTkFont(size=16, weight="bold"))
        legendTitle.pack(pady=(0, 5))

        legendScroll = ctk.CTkScrollableFrame(self.legendFrame, fg_color="#181818")
        legendScroll.pack(fill="both", expand=True, padx=5)
        user_id = self.app.getUserID()
        year = self.yearEntry.get().strip() or None
        dbTable, labels, netValues, incomeValues, expenseValues = prepareChartData(user_id, year, self.typeFilterVar.get())

        if not labels:
            label = ctk.CTkLabel(self.chartFrame, text="No data to display.")
            label.pack()
            return
        
        chartType = self.chartTypeVar.get()
        if chartType == "horizontalbar" and self.typeFilterVar.get() == "income":
            label = ctk.CTkLabel(self.chartFrame, text="No expense data available for 'income' filter.")
            label.pack()
            return
        chartObject = self.chartTypes[chartType][0]
        chartObject.draw(self.chartFrame, dbTable, labels, netValues)

        totalAmount = sum(abs(v) for v in netValues)
        for i, (label, netValue, incomeValue, expenseValue) in enumerate(zip(labels, netValues, incomeValues, expenseValues)):
            categoryFrame = ctk.CTkFrame(legendScroll, fg_color="#303030")
            categoryFrame.pack(fill="x", pady=2, padx=5)

            categoryLabel = ctk.CTkLabel(categoryFrame, text=label, font=ctk.CTkFont(size=12, weight="bold"))
            categoryLabel.pack(anchor="w", padx=5, pady=(5, 0))

            if self.typeFilterVar.get() == "all":
                if incomeValue > 0:
                    incomePercentage = (incomeValue / totalAmount * 100) if totalAmount > 0 else 0
                    incomeText = f"Income: €{incomeValue:,.2f} ({incomePercentage:.1f}%)"
                    ctk.CTkLabel(categoryFrame, text=incomeText, font=ctk.CTkFont(size=12, weight="bold"), text_color="green").pack(anchor="w", padx=5, pady=(0, 2))
                if expenseValue > 0:
                    expensePercentage = (expenseValue / totalAmount * 100) if totalAmount > 0 else 0
                    expenseText = f"Expense: -€{expenseValue:,.2f} ({expensePercentage:.1f}%)"
                    ctk.CTkLabel(categoryFrame, text=expenseText, font=ctk.CTkFont(size=12, weight="bold"), text_color="red").pack(anchor="w", padx=5, pady=(0, 2))
            else:
                value = incomeValue if self.typeFilterVar.get() == "income" else expenseValue
                percentage = (value / totalAmount *100) if totalAmount > 0 else 0
                prefix = "" if self.typeFilterVar.get() == "income" else "-"
                amountText = f"{prefix}€{value:,.2f} ({percentage:.1f}%)"
                color = "green" if self.typeFilterVar.get() == "income" else "red"
                ctk.CTkLabel(categoryFrame, text=amountText, font=ctk.CTkFont(size=12, weight="bold"), text_color=color).pack(anchor="w", padx=5, pady=(0, 2))

    def clearEntries(self):
        self.yearEntry.delete(0, "end")