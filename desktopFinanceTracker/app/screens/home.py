import customtkinter as ctk
import datetime
from app.config import DB_BACKUP_PATH
from database.db import insertTransaction, backupDB
from app.utils.exports import export_transactions_to_csv, export_transactions_to_excel, export_transactions_to_pdf
from app.utils.feedmessages import generateFeedMessages
from CTkMessagebox import CTkMessagebox

class homeScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app
        self.type_var = ctk.StringVar(value="Select")
        self.dateEntry = None
        self.categoryEntry = None
        self.descriptionEntry = None
        self.amountEntry = None
        self.filenameEntry = None
        self.feedFrame = None
        self.feedLabels = []
        self.greetLabel = None

        self.buildUI()

    def buildUI(self):
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)

        ctk.CTkLabel(self, text="Home", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="ew")

        utilityFrame = ctk.CTkFrame(self, fg_color="transparent")
        utilityFrame.grid(row=0, column=0, sticky="sw")
        ctk.CTkButton(utilityFrame, text="Backup Database", command=self.backupDatabase).pack(padx=10)

        addExportFrame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        addExportFrame.grid(row=1, column=1, sticky="nsew")

        self.addTransactionFrame = ctk.CTkFrame(addExportFrame, fg_color="#181818")
        self.addTransactionFrame.grid(row=0, column=0, sticky="nsew", padx=(5, 10), pady=(10, 5))
        ctk.CTkLabel(self.addTransactionFrame, text="Add Transaction", font=ctk.CTkFont(size=24, weight="bold")).pack(padx=10, pady=(10, 0))
        ctk.CTkLabel(self.addTransactionFrame, text="Add income and expense transactions here to begin analysing and visualizing your data using the other features.", font=ctk.CTkFont(size=12), wraplength=300).pack(padx=10, pady=(0, 20))

        ctk.CTkLabel(self.addTransactionFrame, text="Type").pack(pady=5)
        self.type_var = ctk.StringVar(value="Select")
        ctk.CTkOptionMenu(self.addTransactionFrame, variable=self.type_var, values=["income", "expense"], corner_radius=0).pack()

        ctk.CTkLabel(self.addTransactionFrame, text="Date (DD-MM-YYYY)").pack(pady=5)
        self.dateEntry = ctk.CTkEntry(self.addTransactionFrame, placeholder_text="01-01-2025")
        self.dateEntry.pack()

        ctk.CTkLabel(self.addTransactionFrame, text="Category").pack(pady=5)
        self.categoryEntry = ctk.CTkEntry(self.addTransactionFrame, placeholder_text="Bills")
        self.categoryEntry.pack()

        ctk.CTkLabel(self.addTransactionFrame, text="Description").pack(pady=5)
        self.descriptionEntry = ctk.CTkEntry(self.addTransactionFrame, placeholder_text="Rent")
        self.descriptionEntry.pack()

        ctk.CTkLabel(self.addTransactionFrame, text="Amount").pack(pady=5)
        self.amountEntry = ctk.CTkEntry(self.addTransactionFrame, placeholder_text="499.99")
        self.amountEntry.pack()

        addTransactionButtonFrame = ctk.CTkFrame(self.addTransactionFrame, corner_radius=0, fg_color="transparent")
        addTransactionButtonFrame.pack()

        addButton = ctk.CTkButton(addTransactionButtonFrame, text="Add Transaction", command=self.addTransaction, corner_radius=0)
        addButton.pack(side="left", pady=20, padx=5)

        refreshButton = ctk.CTkButton(addTransactionButtonFrame, text="Refresh", command=self.refreshEntries, corner_radius=0, width=35)
        refreshButton.pack(side="left", padx=5)

        self.addTransactionMessageFrame = ctk.CTkFrame(self.addTransactionFrame, height=60, width=600, fg_color="transparent")
        self.addTransactionMessageFrame.pack()
        self.addTransactionMessageFrame.pack_propagate(False)

        exportFrame = ctk.CTkFrame(addExportFrame, fg_color="#181818")
        exportFrame.grid(row=1, column=0, sticky="nsew", padx=(5, 10), pady=(5, 10))
        ctk.CTkLabel(exportFrame, text="Export Transactions", font=ctk.CTkFont(size=24, weight="bold")).pack(padx=10, pady=(10, 0))
        ctk.CTkLabel(exportFrame, text="Used to export data as CSV, Excel or PDF.", font=ctk.CTkFont(size=12)).pack(padx=10, pady=(0, 20))

        ctk.CTkLabel(exportFrame, text="Filename:").pack()
        self.filenameEntry = ctk.CTkEntry(exportFrame, placeholder_text="transactions")
        self.filenameEntry.pack(pady=(0, 20))

        ctk.CTkButton(exportFrame, text="Export to CSV", command=lambda: self.export('csv'), corner_radius=0).pack(pady=5)
        ctk.CTkButton(exportFrame, text="Export to PDF", command=lambda: self.export('pdf'), corner_radius=0).pack(pady=5)
        ctk.CTkButton(exportFrame, text="Export to Excel", command=lambda: self.export('excel'), corner_radius=0).pack(pady=5)

        infoFrame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        infoFrame.grid(row=1, column=0, sticky="nsew")

        self.greetFrame = ctk.CTkFrame(infoFrame, fg_color="#181818")
        self.greetFrame.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=(10, 5))
        today = datetime.datetime.now()
        weekday_name = today.strftime("%A")
        greetingText = f"Happy {weekday_name}, {self.app.currentUser or 'Quest'}!"
        self.greetLabel = ctk.CTkLabel(self.greetFrame, text=greetingText, font=ctk.CTkFont(size=18, weight="bold"))
        self.greetLabel.pack(side="left", anchor=ctk.W, padx=10, pady=(10, 10), fill="x")

        self.feedFrame = ctk.CTkFrame(infoFrame, fg_color="#181818")
        self.feedFrame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(5, 10))
        ctk.CTkLabel(self.feedFrame, text="This month's feed", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor=ctk.W, padx=10, pady=(10, 20))
        self.feedLabels.append(ctk.CTkLabel(self.feedFrame, text="Log in to see feed.", wraplength=800, justify="left"))
        self.feedLabels[-1].pack(anchor=ctk.W, padx=10, pady=5)

        infoFrame.grid_rowconfigure(0, weight=1)
        infoFrame.grid_rowconfigure(1, weight=500)
        infoFrame.grid_columnconfigure(0, weight=1)

        addExportFrame.grid_rowconfigure(0, weight=1)
        addExportFrame.grid_rowconfigure(1, weight=3)
        addExportFrame.grid_columnconfigure(0, weight=1)

    def refreshEntries(self):
        self.type_var.set("Select")
        self.dateEntry.delete(0, "end")
        self.categoryEntry.delete(0, "end")
        self.descriptionEntry.delete(0, "end")
        self.amountEntry.delete(0, "end")

    def updateFeed(self):
        for label in self.feedLabels:
            label.destroy()
        self.feedLabels.clear()

        if self.greetLabel:
            today = datetime.datetime.now()
            weekday_name = today.strftime("%A")
            greetingText = f"Happy {weekday_name}, {self.app.currentUser or 'Quest'}!"
            self.greetLabel.configure(text=greetingText)

        if self.app.currentUser:
            user_id = self.app.getUserID()
            feedMessages = generateFeedMessages(user_id)
            for message in feedMessages:
                label = ctk.CTkLabel(self.feedFrame, text=message, wraplength=800, justify="left")
                label.pack(anchor=ctk.W, padx=10, pady=5)
                self.feedLabels.append(label)
        else:
            label = ctk.CTkLabel(self.feedFrame, text="Log in to see feed.", wraplength=800, justify="left")
            label.pack(anchor=ctk.W, padx=10, pady=5)
            self.feedLabels.append(label)

    def addTransaction(self):
        date = self.dateEntry.get()
        category = self.categoryEntry.get()
        description = self.descriptionEntry.get()
        try:
            amount = float(self.amountEntry.get())
            type_ = self.type_var.get()
        except ValueError:
            error = ctk.CTkLabel(self.addTransactionMessageFrame, text="Invalid amount!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        if not date or not category or not description:
            error = ctk.CTkLabel(self.addTransactionMessageFrame, text="All fields are required!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return
        
        type_value = self.type_var.get()
        if type_value == "Select":
            error = ctk.CTkLabel(self.addTransactionMessageFrame, text="Please select a transaction type!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)
            return

        user_id = self.app.getUserID()
        try:
            insertTransaction(date, category, description, amount, type_, user_id)
            success = ctk.CTkLabel(self.addTransactionMessageFrame, text="Transaction added!", text_color="green")
            success.pack()
            success.after(2000, success.destroy)
            self.updateFeed()
        except ValueError as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")

        self.updateFeed()

    def backupDatabase(self):
        try:
            backupDB()
            CTkMessagebox(title="Success", message=f"Database has been successfully backed up to {DB_BACKUP_PATH}", icon="check")
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Backup failed: {str(e)}", icon="cancel")

    def export(self, formatType):
        user_id = self.app.getUserID()
        filename = self.filenameEntry.get()
        if formatType == 'csv':
            export_transactions_to_csv(user_id, filename)
        elif formatType == 'pdf':
            export_transactions_to_pdf(user_id, filename)
        elif formatType == 'excel':
            export_transactions_to_excel(user_id, filename)
        CTkMessagebox(title="Success", message=f"Exported to {formatType.upper()}!", icon="check")

    def clearEntries(self):
        self.dateEntry.delete(0, "end")
        self.amountEntry.delete(0, "end")
        self.categoryEntry.delete(0, "end")
        self.descriptionEntry.delete(0, "end")
        self.filenameEntry.delete(0, "end")