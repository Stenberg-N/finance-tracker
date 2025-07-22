from database.db import view_all_transactions
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer, PowerTransformer
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
import pandas as pd
import xgboost as xgb

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
    rolling_mean = np.convolve(y, np.ones(3)/3, mode="same").reshape(-1,1)
    x = np.hstack([x, rolling_mean])

    return months, x, y

def run_gridsearch(x, y, pipeline, param_grid):

    cv = TimeSeriesSplit(n_splits=3)

    gridsearch = GridSearchCV(
        pipeline,
        param_grid=param_grid,
        cv=cv,
        verbose=1,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )

    gridsearch.fit(x, y)

    return gridsearch.best_params_

def linear_model():
    months, x, y = get_months_x_y()
    pipeline_linear = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])

    param_grid = [
        {
        'regressor': [LinearRegression()],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()]
        },
        {
        'regressor': [Ridge(), Lasso(max_iter=10000)],
        'regressor__alpha': [0.1, 1, 10, 100, 1000],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()]
        },
        {
        'regressor': [HuberRegressor(max_iter=1000)],
        'regressor__alpha': [0.0001, 0.001, 0.01, 0.1, 1],
        'regressor__epsilon': [1, 1.1, 1.35, 1.5],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()]
        }
    ]

    best_params = run_gridsearch(x, y, pipeline_linear, param_grid)

    best_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])

    best_pipeline.set_params(**best_params)
    best_pipeline.fit(x, y)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_pipeline.predict(next_features)[0]

    return predicted_expense, months, y

def polynomial_model():
    months, x, y = get_months_x_y()
    pipeline_poly = Pipeline([
        ('poly', PolynomialFeatures()),
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression()),
    ])

    param_grid = [
        {
        'regressor': [Ridge(), Lasso(max_iter=10000)],
        'regressor__alpha': [0.1, 1, 10, 100, 1000],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()],
        'poly__degree': [2, 3, 4]
        },
        {
        'regressor': [HuberRegressor(max_iter=1000)],
        'regressor__alpha': [0.0001, 0.001, 0.01, 0.1, 1],
        'regressor__epsilon': [1, 1.1, 1.35, 1.5],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()],
        'poly__degree': [2, 3, 4]
        }
    ]

    best_params = run_gridsearch(x, y, pipeline_poly, param_grid)

    best_pipeline = Pipeline([
        ('poly', PolynomialFeatures()),
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])

    best_pipeline.set_params(**best_params)
    best_pipeline.fit(x, y)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_pipeline.predict (next_features)[0]

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

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])

    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = model.predict (next_features)[0]

    return predicted_expense, months, y

def ensemble_model():
    pred1, months, y = linear_model()
    pred2, _, _ = randomforest_model()
    pred3, _, _ = arima_model()
    pred4, _, _ = xgboost_model()
    ensemble_pred = np.mean([pred1, pred2, pred3, pred4])

    return ensemble_pred, months, y

def xgboost_model():
    months, x, y = get_months_x_y()

    model= xgb.XGBRegressor()
    model.fit(x, y)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])

    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = model.predict (next_features)[0]

    return predicted_expense, months, y
