import customtkinter as ctk
from app.screens.login import loginScreen
from app.screens.register import registerScreen
from app.screens.home import homeScreen
from app.screens.transactions import transactionsScreen
from app.screens.chartselection import chartsScreen
from app.screens.deleteData import deleteDataScreen
from app.screens.deleteAccount import deleteAccountScreen
from app.screens.predictions import predictionScreen
from CTkMessagebox import CTkMessagebox
from database.db import getUserID, verifyLogin, clearEncryptionKey

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("custom")

class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Finance Tracker")
        self.geometry("1600x980")
        self.currentUser = None

        self.mainFrame = ctk.CTkFrame(self, corner_radius=0)
        self.mainFrame.pack(fill="both", expand=True)
        self.buttonFrame = ctk.CTkFrame(self.mainFrame, corner_radius=0, fg_color="#181818")
        self.buttonFrame.grid(row=0, column=0, sticky="ns")
        self.contentFrame = ctk.CTkFrame(self.mainFrame, corner_radius=0, fg_color="#101010")
        self.contentFrame.grid(row=0, column=1, sticky="nsew")

        self.mainFrame.grid_columnconfigure(0, weight=0)
        self.mainFrame.grid_columnconfigure(1, weight=1)
        self.mainFrame.grid_rowconfigure(0, weight=1)

        self.frames = {
            "login": loginScreen(self.contentFrame, self),
            "register": registerScreen(self.contentFrame, self),
            "home": homeScreen(self.contentFrame, self),
            "transactions": transactionsScreen(self.contentFrame, self),
            "charts": chartsScreen(self.contentFrame, self),
            "deleteData": deleteDataScreen(self.contentFrame, self),
            "deleteAccount": deleteAccountScreen(self.contentFrame, self),
            "predictions": predictionScreen(self.contentFrame, self)
        }

        self.sidebarButtons = {}
        self.hideSidebar()
        self.showFrame("login")

    def showFrame(self, frameName):
        if frameName == "login":
            self.frames["login"] = loginScreen(self.contentFrame, self)

        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frameName].grid(sticky="nsew", padx=10, pady=10)
        self.contentFrame.grid_rowconfigure(0, weight=1)
        self.contentFrame.grid_columnconfigure(0, weight=1)

        if frameName == "login":
            self.frames["login"].clearEntries()
        elif frameName == "register":
            self.frames["register"].clearEntries()

        if frameName not in ["login", "register"]:
            self.showSidebar()
            if frameName == "home" and self.currentUser:
                self.frames["home"].updateFeed()
            elif frameName == "transactions" and self.currentUser:
                self.frames["transactions"].updateTable()
            elif frameName == "predictions" and self.currentUser:
                self.frames["predictions"].buildUI()
        else:
            self.hideSidebar()

    def showSidebar(self):
        if not self.sidebarButtons:
            self.sidebarButtons["home"] = ctk.CTkButton(self.buttonFrame, text="Home", command=lambda: self.showFrame("home"), corner_radius=0, height=60, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["transactions"] = ctk.CTkButton(self.buttonFrame, text="Show transactions", command=lambda: self.showFrame("transactions"), corner_radius=0, height=60, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["charts"] = ctk.CTkButton(self.buttonFrame, text="Charts", command=lambda: self.showFrame("charts"), corner_radius=0, height=60, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["predictions"] = ctk.CTkButton(self.buttonFrame, text="Predictions", command=lambda:self.showFrame("predictions"), corner_radius=0, height=60, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["deleteAccount"] = ctk.CTkButton(self.buttonFrame, text="Delete account", command=lambda: self.showFrame("deleteAccount"), corner_radius=0, height=40, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["deleteData"] = ctk.CTkButton(self.buttonFrame, text="Delete data", command=lambda: self.showFrame("deleteData"), corner_radius=0, height=40, fg_color="#303030", hover_color="#252525")
            self.sidebarButtons["logout"] = ctk.CTkButton(self.buttonFrame, text="Logout", command=self.logout, corner_radius=0, height=40, fg_color="#303030", hover_color="#252525")

            for key in ["home", "transactions", "charts", "predictions"]:
                self.sidebarButtons[key].pack(side="top", fill="both", pady=(0, 5))

            spacer = ctk.CTkFrame(self.buttonFrame, fg_color="transparent", width=80)
            spacer.pack(side="top", fill="both", expand=True)

            for key in ["logout", "deleteData", "deleteAccount"]:
                self.sidebarButtons[key].pack(side="bottom", fill="both", pady=(5, 0))

        self.buttonFrame.grid(row=0, column=0, sticky="ns")

    def hideSidebar(self):
        self.buttonFrame.grid_forget()

    def login(self, username, password):
        if verifyLogin(username, password):
            self.currentUser = username
            self.showFrame("home")
            self.frames["home"].updateFeed()
            return True
        return False

    def logout(self):
        self.currentUser = None
        clearEncryptionKey()
        self.hideSidebar()
        self.frames["login"].clearEntries()
        self.frames["register"].clearEntries()
        self.frames["transactions"].clearEntries()
        self.frames["home"].clearEntries()
        self.frames["charts"].clearEntries()
        self.frames["deleteData"].clearEntries()
        self.frames["deleteAccount"].clearEntries()
        self.frames["predictions"].clearEntries()
        self.showFrame("login")

    def getUserID(self):
        return getUserID(self.currentUser)

    def requireLogin(self, func):
        def wrapper(*args, **kwargs):
            if self.currentUser is None:
                CTkMessagebox(title="Error", message="Please log in!", icon="cancel")
                self.showFrame("login")
                return
            return func(*args, **kwargs)
        return wrapper

    def runPredictionModel(self, model_type, n_future_months=1):
        if not self.currentUser:
            return None

        user_id = self.getUserID()
        if user_id is None:
            return None

        try:
            from app.ml.linear import linear_model
            from app.ml.polynomial import polynomial_model
            from app.ml.sarimax import sarimax_model
            from app.ml.randomforest import randomforest_model
            from app.ml.xgboost import xgboost_model
            from app.ml.ensemble import ensemble_model

            if model_type == 'linear':
                model = linear_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            elif model_type == 'polynomial':
                model = polynomial_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            elif model_type == 'sarimax':
                model = sarimax_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            elif model_type == 'randomforest':
                model = randomforest_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            elif model_type == 'xgboost':
                model = xgboost_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            elif model_type == 'ensemble':
                model = ensemble_model(n_future_months=n_future_months, user_id=user_id)
                return model.predict()
            else:
                raise ValueError(f"Unknown model type: {model_type}")

        except Exception as e:
            print(f"ML Error in {model_type}: {str(e)}")
            return None

    def get_user_context(self):
        if not self.currentUser:
            return None
        return self.getUserID()