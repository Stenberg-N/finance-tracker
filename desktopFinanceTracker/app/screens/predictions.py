import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import numpy as np
import threading
from CTkMessagebox import CTkMessagebox
import matplotlib.pyplot as plt

PREDICTION_MODEL_DESCRIPTIONS = {
    'linear': "Linear Regression: A simple yet effective model that assumes a linear relationship between past expenses and future predictions. Best for stable and gradually changing spending patterns. Fast and interpretable, but may struggle with seasonal trends or sudden changes.",
    'polynomial': "Polynomial Regression: Extends linear regression by capturing non-linear trends and curves in your spending data. Good for expenses that follow more complex patterns over time. More flexible than linear but can overfit with limited data.",
    'sarimax': "SARIMAX (Seasonal ARIMA): A sophisticated time series model that excels at capturing seasonal patterns and trends in your monthly expenses. Ideal for data with yearly cycles. Computationally intensive but very accurate for seasonal data.",
    'randomforest': "Random Forest: An ensemble method that builds multiple decision trees and averages their predictions. Robust to outliers and handles complex, non-linear relationships well. Good balance of accuracy and resistance to overfitting.",
    'ensemble': "Ensemble Model: Combines predictions from Linear, Polynomial, SARIMAX, and XGBoost models using simple averaging. Aims to leverage the strengths of each model while reducing individual weaknesses. Often provides the most stable predictions.",
    'xgboost': "XGBoost: A powerful gradient boosting algorithm that iteratively improves predictions by learning from previous errors. Excellent for complex patterns and sparse data. Highly accurate but can be prone to overfitting without proper tuning."
}

max_past_n_months = 12 # Limit the amount of actual expense points shown in the graph so that the graph doesn't overfill.

def draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, parent_frame):
    plt.style.use('dark_background')
    fig = Figure(figsize=(10, 9), dpi=100, facecolor="#101010")
    ax = fig.add_subplot(111)

    actuals = np.array(actuals, dtype=float)
    if len(months_labels) > max_past_n_months:
        months_labels = months_labels[-max_past_n_months:]
        actuals = actuals[-max_past_n_months:]

    predicted_expense = np.array([predicted_expense] if np.isscalar(predicted_expense) else predicted_expense, dtype=float).flatten()
    next_month = datetime.datetime.strptime(months_labels[-1], "%b %Y")
    future_labels = []
    for i in range(len(predicted_expense)):
        future_month = (next_month + datetime.timedelta(days=31 * (i+1))).replace(day=1)
        future_labels.append(future_month.strftime("%b %Y"))

    ax.plot(months_labels, actuals, marker='o', label="Actual expenses", color="blue")
    ax.plot([months_labels[-1]] + future_labels, [actuals[-1]] + list(predicted_expense), marker='o', linestyle="--", color="orange", label="Predicted expenses")
    ax.scatter(future_labels, predicted_expense, color="red", zorder=5)

    last_y = None
    texts = []
    for label, pred in zip(future_labels, predicted_expense):
        y_offset = 10
        if last_y is not None and abs(pred - last_y) < 100:
            y_offset += 50
        texts.append(
            ax.annotate(f"Predicted: €{pred:.2f}", xy=(label, pred), xytext=(0, y_offset), textcoords="offset points", ha="center", color="red", arrowprops=dict(arrowstyle="->", color="gray"))
        )
        last_y = pred

    ax.set_xlabel("Month")
    ax.set_ylabel("Expenses (€)")
    ax.set_title("Monthly expenses & prediction")
    ax.set_yticks(np.arange(min(actuals), max(actuals) + max(predicted_expense) + 500, 500))
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(expand=True, fill="both")
    widget.is_chart_widget = True

class predictionScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="#101010")
        self.app = app

        self.buildUI()

    def buildUI(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Prediction models", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0))
        ctk.CTkLabel(self,
                     text="Different machine learning models that make predictions based on your data in your database. For the models to make acceptable predictions, they require a certain amount of data.",
                     justify="left").pack()
        
        descriptionFrame = ctk.CTkFrame(self, height=1, fg_color="transparent")
        descriptionFrame.pack(fill="x")
        descriptionFrame.pack_propagate(False)
        
        self.description_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=18), wraplength=1200, justify="left")
        self.description_label.pack(pady=(5, 20))
        
        self.optionFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.optionFrame.pack(anchor=ctk.W, padx=20, pady=5)

        frames = {
            "modelSelection": ctk.CTkFrame(self.optionFrame, fg_color="transparent"),
            "pastMonths": ctk.CTkFrame(self.optionFrame, fg_color="transparent"),
            "predictMonths": ctk.CTkFrame(self.optionFrame, fg_color="transparent"),
            "predictButton": ctk.CTkFrame(self.optionFrame, fg_color="transparent"),
            "modelMSE": ctk.CTkFrame(self.optionFrame, fg_color="transparent"),
            "infoButton": ctk.CTkFrame(self.optionFrame, fg_color="transparent")
        }
        
        for frame in frames.values():
            frame.pack(padx=5, side="left")

        self.prediction_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.prediction_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.prediction_frame, text="Note that depending on the chosen model and the amount of months to predict, the time to make the predictions can take some time! Please wait until the graph appears.",
                     font=ctk.CTkFont(size=12), wraplength=600, justify="left").pack(pady=(180, 10))

        ctk.CTkLabel(frames["modelSelection"], text="Select Model:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        self.model = ctk.StringVar(value="linear")
        self.modelMenu = ctk.CTkOptionMenu(
            frames["modelSelection"],
            variable=self.model,
            values=["linear", "polynomial", "sarimax", "randomforest", "ensemble", "xgboost"],
            command=self.onModelSelect,
            corner_radius=0
        )
        self.modelMenu.pack(side="left")

        self.updateModelDescription("linear")

        ctk.CTkLabel(frames["pastMonths"], text="Past months to show:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        self.past_month_entry = ctk.CTkEntry(frames["pastMonths"], width=40, placeholder_text="3")
        self.past_month_entry.pack(side="left")
        ctk.CTkLabel(self.prediction_frame, text="Leaving the entry for past months empty will default to the past 12 months. Does not affect the predictions. Use to prevent the graph from overfilling if there are years of transaction data that it would then try to fit in.",
                     wraplength=600, font=ctk.CTkFont(size=12)).pack(pady=5)

        ctk.CTkLabel(frames["predictMonths"], text="Months to predict:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        self.month_entry = ctk.CTkEntry(frames["predictMonths"], width=40, placeholder_text="3")
        self.month_entry.pack(side="left")

        self.predict_btn = ctk.CTkButton(frames["predictButton"], text="Predict", command=self.on_predict, width=40, fg_color="#349c30", hover_color="#1f5f1d")
        self.predict_btn.pack()

        self.mseLabel = ctk.CTkLabel(frames["modelMSE"], text="Model MSE", font=ctk.CTkFont(size=12))
        self.mseLabel.pack(padx=30)

        infoButton = ctk.CTkButton(frames["infoButton"], text="Info", command=lambda: MSEinfoBox(), font=ctk.CTkFont(size=12), corner_radius=0, width=30)
        infoButton.pack(padx=10)

        def MSEinfoBox():
            CTkMessagebox(
                title="MSE Info",
                message="MSE, abbreviated from mean squared error, is a mathematical metric that is used to measure the average squared difference between predicted values from a model and the actual target values in a dataset." \
                " It essentially tells how off the model's predictions are.\n" \
                "The closer the value is to 0, the closer the fit of the model to the data is, as in the results are closer to true values. The value of MSE cannot go below 0.")

    def onModelSelect(self, prediction_type):
        self.current_prediction_type = prediction_type
        self.updateModelDescription(prediction_type)

    def updateModelDescription(self, prediction_type):
        description = PREDICTION_MODEL_DESCRIPTIONS.get(prediction_type, "No description available for this model.")
        self.description_label.configure(text=description)

    def on_predict(self):
        global max_past_n_months

        try:
            n_months = int(self.month_entry.get())
            if n_months < 1:
                raise ValueError
        except ValueError:
            error = ctk.CTkLabel(self.prediction_frame, text="Please enter a valid positive integer.", text_color="red")
            error.pack()
            error.after(2000, lambda: error.destroy())
            return

        past_n_months = self.past_month_entry.get()
        if past_n_months == "":
            past_n_months = max_past_n_months
        else:
            try:
                past_n_months = int(past_n_months)
                max_past_n_months = past_n_months
            except ValueError:
                error = ctk.CTkLabel(self.prediction_frame, text="Please enter a valid positive integer.", text_color="red")
                error.pack()
                error.after(2000, lambda: error.destroy())
                return

        for widget in self.prediction_frame.winfo_children():
            if hasattr(widget, "is_chart_widget") and widget.is_chart_widget:
                widget.destroy()

        prediction_type = self.model.get()

        def run_ml():
            result = self.app.runPredictionModel(model_type=prediction_type, n_future_months=n_months)

            if result is None:
                self.app.after(0, lambda: self.showError("Prediction failed. Please ensure you have enough data and are logged in."))
                return
            
            predicted_expense, months, actuals, mse = result

            months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]
            next_month = (datetime.datetime.strptime(months[-1], "%Y-%m") + datetime.timedelta(days=31)).replace(day=1)
            next_month_label = next_month.strftime("%b %Y")

            def updateUI():
                self.draw_and_pack_plot(months_labels, actuals, predicted_expense, next_month_label, mse)

            self.app.after(0, updateUI)

        threading.Thread(target=run_ml, daemon=True).start()

    def clear_prediction_frame(self):
        for widget in list(self.prediction_frame.winfo_children()):
            widget.destroy()

    def showError(self, message):
        error = ctk.CTkLabel(self.prediction_frame, text=message, text_color="red")
        error.pack(pady=10)
        error.after(3000, lambda: error.destroy())

    def draw_and_pack_plot(self, months_labels, actuals, predicted_expense, next_month_label, mse):
        self.clear_prediction_frame()
        draw_prediction_plot(months_labels, actuals, next_month_label, predicted_expense, self.prediction_frame)
        self.mseLabel.configure(text=f"Model MSE: {mse:.2f}")

    def clearEntries(self):
        self.month_entry.delete(0, "end")
        self.past_month_entry.delete(0, "end")