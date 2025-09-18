import customtkinter as ctk
from database.db import deleteUser, clearEncryptionKey

class deleteAccountScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app

        self.buildUI()

    def buildUI(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=20)

        ctk.CTkLabel(self, text="Delete Account", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        self.deleteAccountFrame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.deleteAccountFrame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.deleteAccountFrame, text="Enter your password to confirm account deletion.").pack(pady=(20, 0))
        self.passwordEntry = ctk.CTkEntry(self.deleteAccountFrame, show="*")
        self.passwordEntry.pack()

        ctk.CTkButton(self.deleteAccountFrame, text="Confirm Delete", command=self.confirm_user_deletion, corner_radius=0).pack(pady=(40, 5))
        ctk.CTkButton(self.deleteAccountFrame, text="Cancel", command=self.handleCancel, corner_radius=0).pack(pady=5)

    def handleCancel(self):
        self.passwordEntry.delete(0, "end")
        self.app.showFrame("home")

    def confirm_user_deletion(self):
        password = self.passwordEntry.get()
        currentUser = self.app.currentUser
        if not password:
            error = ctk.CTkLabel(self.deleteAccountFrame, text="Please enter your password to delete your account!", text_color="red")
            error.pack()
            error.after(5000, error.destroy)
            return

        success, message = deleteUser(currentUser, password)

        if success:
            self.app.showFrame("login")
            loginFrame = self.app.frames["login"]
            try:
                targetFrame = loginFrame.centerFrame
            except AttributeError:
                targetFrame = loginFrame
            currentUser = None
            clearEncryptionKey()
            success = ctk.CTkLabel(targetFrame, text=message, text_color="green")
            success.pack(pady=20)
            success.after(5000, success.destroy)
        else:
            error = ctk.CTkLabel(self.deleteAccountFrame, text=message, text_color="red")
            error.pack(pady=20)
            error.after(5000, error.destroy)

    def clearEntries(self):
        self.passwordEntry.delete(0, "end")