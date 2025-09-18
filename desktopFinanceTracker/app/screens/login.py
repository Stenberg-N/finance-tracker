import customtkinter as ctk

class loginScreen(ctk.CTkFrame):
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

        ctk.CTkLabel(headerFrame, text="Login", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(headerFrame, text="Please log in.", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        ctk.CTkLabel(self.centerFrame, text="Username:", font=ctk.CTkFont(size=14)).pack(pady=(50, 5))
        self.usernameEntry = ctk.CTkEntry(self.centerFrame, placeholder_text="Username")
        self.usernameEntry.pack()
        ctk.CTkLabel(self.centerFrame, text="Password:", font=ctk.CTkFont(size=14)).pack(pady=(20, 5))
        self.passwordEntry = ctk.CTkEntry(self.centerFrame, show="*", placeholder_text="Password")
        self.passwordEntry.pack()
        self.passwordEntry.bind("<Return>", lambda _: self.handleLogin())
        ctk.CTkButton(self.centerFrame, text="Login", command=self.handleLogin, corner_radius=0).pack(pady=(50, 5))
        ctk.CTkButton(self.centerFrame, text="Register", command=lambda: self.app.showFrame("register"), corner_radius=0).pack(pady=5)

    def handleLogin(self):
        username = self.usernameEntry.get()
        password = self.passwordEntry.get()

        if not username or not password:
            error = ctk.CTkLabel(self.centerFrame, text="Enter username and/or password!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)

        if self.app.login(username, password):
            success = ctk.CTkLabel(self.centerFrame, text="Login successful!", text_color="green")
            success.pack()
            success.after(2000, success.destroy)
            lambda: self.app.showFrame("home")
        else:
            error = ctk.CTkLabel(self.centerFrame, text="Invalid username or password!", text_color="red")
            error.pack()
            error.after(2000, error.destroy)

    def clearEntries(self):
        self.usernameEntry.delete(0, "end")
        self.passwordEntry.delete(0, "end")