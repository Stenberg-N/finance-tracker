import customtkinter as ctk
from database.db import insertUser

class registerScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        headerFrame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=0)
        headerFrame.grid(row=0, column=0, sticky="ew")

        self.centerFrame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.centerFrame.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(headerFrame, text="Register", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(headerFrame, text="Register and make an account here.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        ctk.CTkLabel(self.centerFrame, text="Username:", font=ctk.CTkFont(size=14)).pack(pady=(50, 5))
        self.usernameEntry = ctk.CTkEntry(self.centerFrame, placeholder_text="Username")
        self.usernameEntry.pack()

        ctk.CTkLabel(self.centerFrame, text="Password:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.passwordEntry = ctk.CTkEntry(self.centerFrame, show="*", placeholder_text="Password")
        self.passwordEntry.pack()

        ctk.CTkLabel(self.centerFrame, text="Confirm Password:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.confirmPasswordEntry = ctk.CTkEntry(self.centerFrame, show="*", placeholder_text="Password")
        self.confirmPasswordEntry.pack()

        ctk.CTkButton(self.centerFrame, text="Register", command=self.handleRegister, corner_radius=0).pack(pady=(50, 5))
        ctk.CTkButton(self.centerFrame, text="Back to Login", command=lambda: self.app.showFrame("login"), corner_radius=0).pack(pady=5)

    def handleRegister(self):
        username = self.usernameEntry.get()
        password = self.passwordEntry.get()
        confirmPassword = self.confirmPasswordEntry.get()

        if not username or not password:
            error = ctk.CTkLabel(self.centerFrame, text="Username and password cannot be empty!", text_color="red")
            error.pack()
            error.after(3000, error.destroy)
            return

        if password != confirmPassword:
            error = ctk.CTkLabel(self.centerFrame, text="Passwords do not match!", text_color="red")
            error.pack()
            error.after(3000, error.destroy)
            return

        success = insertUser(username, password)
        if success:
            self.app.showFrame("login")
            loginFrame = self.app.frames["login"]
            try:
                targetFrame = loginFrame.centerFrame
            except AttributeError:
                targetFrame = loginFrame

            success = ctk.CTkLabel(targetFrame, text="Registration successful! Please log in.", text_color="green")
            success.pack(pady=20)
            success.after(3000, success.destroy)
            self.clearEntries()
        else:
            error = ctk.CTkLabel(self.centerFrame, text="Registration failed!", text_color="red")
            error.pack()
            error.after(3000, error.destroy)

    def clearEntries(self):
        self.usernameEntry.delete(0, "end")
        self.passwordEntry.delete(0, "end")
        self.confirmPasswordEntry.delete(0, "end")