from database.db import view_all_transactions
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge
from sklearn.preprocessing import PolynomialFeatures
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor

def fetch_data():
    rows = view_all_transactions()
    monthly_expenses = {}

    for row in rows:
        date = row[1]
        amount = row[4]
        type_ = row[5]
        if type_ == "expense":
            date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
            month_key = date_obj.strftime("%Y-%m")
            monthly_expenses.setdefault(month_key, 0)
            monthly_expenses[month_key] += abs(amount)

    return monthly_expenses

def get_months_x_y():
    monthly_expenses = fetch_data()

    months = sorted(monthly_expenses.keys())
    x = np.arange (len(months)).reshape(-1, 1)
    y = np.array([monthly_expenses[month] for month in months])

    return months, x, y

def linear_model():
    months, x, y = get_months_x_y()

    model = LinearRegression()
    model.fit(x, y)

    next_month_index = len(months)
    predicted_expense = model.predict ([[next_month_index]])[0]

    return predicted_expense, months, y

def polynomial_model():
    months, x, y = get_months_x_y()

    poly = PolynomialFeatures(degree=2)
    x_poly = poly.fit_transform(x)
    model = LinearRegression()
    model.fit(x_poly, y)

    next_month_index = np.array([[len(months)]])
    next_month_poly = poly.transform(next_month_index)
    predicted_expense = model.predict(next_month_poly)[0]

    return predicted_expense, months, y

def robust_linear_model():
    months, x, y = get_months_x_y()

    model = HuberRegressor()
    model.fit(x, y)

    next_month_index = len(months)
    predicted_expense = model.predict([[next_month_index]])[0]

    return predicted_expense, months, y

def ridge_model():
    months, x, y = get_months_x_y()

    model = Ridge(alpha=1.0)
    model.fit(x, y)

    next_month_index = len(months)
    predicted_expense = model.predict([[next_month_index]])[0]

    return predicted_expense, months, y

def arima_model():
    months, x, y = get_months_x_y()

    model = ARIMA(y, order=(1,1,1))
    model_fit = model.fit()
    predicted_expense = model_fit.forecast()[0]

    return predicted_expense, months, y

def randomforest_model():
    months, x, y = get_months_x_y()

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(x, y)

    next_month_index = np.array([[len(months)]])
    predicted_expense = model.predict(next_month_index)[0]

    return predicted_expense, months, y

def ensemble_model():
    pred1, months, y = ridge_model()
    pred2, _, _ = randomforest_model()
    pred3, _, _ = arima_model()
    ensemble_pred = np.mean([pred1, pred2, pred3])

    return ensemble_pred, months, y