import customtkinter as ctk
import tkinter as tk
import datetime
from database.db import viewAllTransactions, deleteTransactionsByID
from CTkMessagebox import CTkMessagebox

class transactionsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app
        self.tree = None
        self.searchbarEntry = None

        self.buildUI()

    def buildUI(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)

        ctk.CTkLabel(self, text="All Transactions", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(self, text="A table consisting of all your income and expense data.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        searchbarFrame = ctk.CTkFrame(self, fg_color="transparent")
        searchbarFrame.pack(padx=20, pady=5, anchor=ctk.E)
        searchbarFrame.grid_columnconfigure(1, weight=1)

        style = tk.ttk.Style()
        style.theme_use("clam")
        style.layout("Edge.Treeview", [("Edge.Treeview.treearea", {"sticky": "nsew"})])
        style.configure("Edge.Treeview", highlightthickness=0, bd=0)
        style.configure("Treeview", background="#181818", foreground="white", fieldbackground="#181818")
        style.configure("Treeview.Heading", relief="none", background="#303030", foreground="white", fieldbackground="#303030")
        style.map("Treeview.Heading", background=[('active', '#252525')])

        columns = ("c1", "c2", "c3", "c4", "c5", "c6")
        self.tree = tk.ttk.Treeview(self, column=columns, show="headings", style="Edge.Treeview")
        headers = ["ID", "Date", "Category", "Description", "Amount", "Type"]

        def treeviewSortColumn(tv, col, col_index, reverse):
            data = [(tv.set(k, col), k) for k in tv.get_children("")]
            if col == "c2":
                try:
                    data.sort(key=lambda t: datetime.datetime.strptime(t[0], "%d-%m-%Y"), reverse=reverse)
                except Exception:
                    data.sort(reverse=reverse)
            else:
                try:
                    data.sort(key=lambda t: float(t[0].replace(",", "").replace("€", "")), reverse=reverse)
                except ValueError:
                    data.sort(reverse=reverse)
            for index, (val, k) in enumerate(data):
                tv.move(k, "", index)
            tv.heading(col, command=lambda: treeviewSortColumn(tv, col, col_index, not reverse))

        for idx, (col, header) in enumerate(zip(columns, headers)):
            self.tree.heading(col, text=header, command=lambda _col=col, _idx=idx: treeviewSortColumn(self.tree, _col, _idx, False))
            self.tree.column(col, anchor=ctk.CENTER)

        self.tree.pack(expand=True, fill="both")

        deleteButton = ctk.CTkButton(searchbarFrame, text="Delete", font=ctk.CTkFont(size=12), fg_color="#D10000", hover_color="#9B0000", width=60, command=self.deleteSelectedTransactions)
        deleteButton.grid(row=0, column=0, padx=(0, 10), sticky="w")

        searchbarLabel = ctk.CTkLabel(searchbarFrame, text="Search:", font=ctk.CTkFont(size=12))
        searchbarLabel.grid(row=0, column=1, padx=(0, 2), sticky="w")

        self.searchbarEntry = ctk.CTkEntry(searchbarFrame, width=150, corner_radius=0, placeholder_text="Groceries")
        self.searchbarEntry.grid(row=0, column=2, padx=(3, 0), sticky="ew")
        self.searchbarEntry.bind("<KeyRelease>", self.filterTableBySearch)

    def fillTable(self, data=None):
        if not self.app.currentUser:
            self.tree.delete(*self.tree.get_children())
            return
        user_id = self.app.getUserID()
        all_rows = viewAllTransactions(user_id)
        self.tree.delete(*self.tree.get_children())
        data = data if data is not None else all_rows
        for row in data:
            self.tree.insert("", ctk.END, values=row)

    def filterTableBySearch(self, event=None):
        if not self.app.currentUser:
            return
        user_id = self.app.getUserID()
        all_rows = viewAllTransactions(user_id)
        query = self.searchbarEntry.get().strip().lower()
        if not query:
            self.fillTable(all_rows)
            return
        filteredData = [row for row in all_rows if any(query in str(cell).lower() for cell in row)]
        self.fillTable(filteredData)

    def deleteSelectedTransactions(self):
        selected_items = self.tree.selection()
        if not selected_items:
            CTkMessagebox(title="Nothing selected", message="Please select at least one transaction to delete.", icon="info")
            return

        idsToDelete = [int(self.tree.item(item, "values")[0]) for item in selected_items]

        confirmation = CTkMessagebox(title="Confirm delete", message=f"Delete {len(idsToDelete)} selected transaction(s)?", icon="warning", option_1="Cancel", option_2="Delete").get()
        if confirmation != "Delete":
            return

        user_id = self.app.getUserID()
        deleteTransactionsByID(user_id, idsToDelete)
        self.fillTable()
        self.app.frames["home"].updateFeed()

    def updateTable(self):
        self.fillTable()

    def clearEntries(self):
        self.searchbarEntry.delete(0, "end")