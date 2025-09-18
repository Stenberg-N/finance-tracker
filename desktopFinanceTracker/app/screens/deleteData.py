import customtkinter as ctk
from database.db import clearAllTransactions


class deleteDataScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app

        self.buildUI()

    def buildUI(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)

        ctk.CTkLabel(self, text="Delete all data", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        self.dataDeleteFrame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.dataDeleteFrame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.dataDeleteFrame, text="Are you sure you want to delete all data? If you are, type 'DELETE ALL DATA' in the text box and hit the delete button:", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.deleteDataEntry = ctk.CTkEntry(self.dataDeleteFrame)
        self.deleteDataEntry.pack()

        ctk.CTkButton(self.dataDeleteFrame, text="Delete", command=self.delete_data, fg_color="#D10000", hover_color="#9B0000", corner_radius=0).pack(pady=40)

    def delete_data(self):
        user_id = self.app.getUserID()
        data_deletion = self.deleteDataEntry.get()

        if data_deletion == str("DELETE ALL DATA"):
            clearAllTransactions(user_id)
            success = ctk.CTkLabel(self.dataDeleteFrame, text="All data successfully deleted!", text_color="green", font=ctk.CTkFont(size=16, weight="bold"))
            success.pack()
            success.after(5000, success.destroy)
        else:
            error = ctk.CTkLabel(self.dataDeleteFrame, text="Invalid confirmation! Data not deleted!", text_color="red", font=ctk.CTkFont(size=16, weight="bold"))
            error.pack()
            error.after(5000, error.destroy)

    def clearEntries(self):
        self.deleteDataEntry.delete(0, "end")