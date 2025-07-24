from database.db import view_all_transactions
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer, PowerTransformer
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
import xgboost as xgb
from itertools import product
import pandas as pd

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
    rolling_mean = pd.Series(y).rolling(window=3, center=True).mean()
    rolling_mean = rolling_mean.bfill().ffill()
    if rolling_mean.isna().any():
        raise ValueError("Still NaNs after fill — check y input.")
    rolling_mean = rolling_mean.values.reshape(-1, 1)
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
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
        },
        {
            'regressor': [Ridge(), Lasso(max_iter=10000)],
            'regressor__alpha': [0.1, 1, 10, 100, 1000],
            'regressor__fit_intercept': [True, False],
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
        },
        {
            'regressor': [HuberRegressor(max_iter=1000)],
            'regressor__alpha': [0.0001, 0.001, 0.01, 0.1, 1],
            'regressor__epsilon': [1, 1.1, 1.35, 1.5],
            'regressor__fit_intercept': [True, False],
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
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
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()],
            'poly__degree': [2, 3, 4]
        },
        {
            'regressor': [HuberRegressor(max_iter=10000)],
            'regressor__alpha': [0.0001, 0.001, 0.01, 0.1, 1],
            'regressor__epsilon': [1, 1.1, 1.35, 1.5],
            'regressor__fit_intercept': [True, False],
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()],
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
    predicted_expense = best_pipeline.predict(next_features)[0]

    return predicted_expense, months, y

def sarimax_model():
    months, x, y = get_months_x_y()

    p_values = range(0, 3)
    d_values = range(0, 2)
    q_values = range(0, 3)
    order_combinations = list(product(p_values, d_values, q_values))

    P_values = range(0, 3)
    D_values = range(0, 2)
    Q_values = range(0, 3)
    s_values = [6, 12]
    seasonal_order_combinations = list(product(P_values, D_values, Q_values, s_values))

    best_aic = np.inf
    best_order = None
    best_seasonal_order = None
    best_model = None

    for order in order_combinations:
        for seasonal_order in seasonal_order_combinations:
            try:
                model = SARIMAX(endog=y, exog=x, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
                results = model.fit(disp=False)
                if results.aic < best_aic:
                    best_aic = results.aic
                    best_order = order
                    best_seasonal_order = seasonal_order
                    best_model = results
            except Exception:
                continue

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_model.forecast(steps=1, exog=next_features)[0]

    return predicted_expense, months, y

def randomforest_model():
    months, x, y = get_months_x_y()

    pipeline_randomforest = Pipeline([
        ('regressor', RandomForestRegressor())
    ])

    param_grid = {
        'regressor__n_estimators': [100, 200],
        'regressor__max_depth': [None, 5, 10],
        'regressor__min_samples_split': [2, 5],
        'regressor__min_samples_leaf': [1, 2],
        'regressor__max_features': [1.0, 'sqrt', 'log2'],
        'regressor__bootstrap': [False, True]
    }

    best_params = run_gridsearch(x, y, pipeline_randomforest, param_grid)

    best_pipeline = Pipeline([
    ('regressor', RandomForestRegressor())
    ])

    best_pipeline.set_params(**best_params)
    best_pipeline.fit(x, y)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_pipeline.predict(next_features)[0]

    return predicted_expense, months, y

def ensemble_model():
    pred1, months, y = linear_model()
    pred2, _, _ = randomforest_model()
    pred3, _, _ = sarimax_model()
    pred4, _, _ = xgboost_model()
    ensemble_pred = np.mean([pred1, pred2, pred3, pred4])

    return ensemble_pred, months, y

def xgboost_model():
    months, x, y = get_months_x_y()

    pipeline_xgb = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', xgb.XGBRegressor(
            objective="reg:squarederror",
            early_stopping_rounds=10,
            eval_metric="rmse"))
    ])

    param_grid = {
        'regressor__n_estimators': [50, 100, 150],
        'regressor__learning_rate': [0.01, 0.1, 0.3],
        'regressor__booster': ['gbtree', 'gblinear', 'dart'],
        'regressor__lambda': [0, 1, 5, 10, 100],
        'regressor__alpha': [0, 1, 5, 10],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()]
    }

    tscv = TimeSeriesSplit(n_splits=3)

    for train_index, test_index in tscv.split(x):
        x_train_full, x_test = x[train_index], x[test_index]
        y_train_full, y_test = y[train_index], y[test_index]

        val_split = int(len(x_train_full) * 0.9)
        x_train, x_val = x_train_full[:val_split], x_train_full[val_split:]
        y_train, y_val = y_train_full[:val_split], y_train_full[val_split:]

    def run_gridsearch_with_early_stopping(x_train, y_train, x_val, y_val, pipeline, param_grid):
        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=tscv,
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        grid_search.fit(
            x_train, y_train,
            regressor__eval_set=[(x_val, y_val)],
            regressor__verbose=1
        )
        return grid_search.best_params_

    best_params = run_gridsearch_with_early_stopping(x_train, y_train, x_val, y_val, pipeline_xgb, param_grid)

    best_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', xgb.XGBRegressor(
            objective="reg:squarederror",
            eval_metric="rmse",
            early_stopping_rounds=10))
    ])

    best_pipeline.set_params(**best_params)
    best_pipeline.fit(
        x_train, y_train,
        regressor__eval_set=[(x_val, y_val)],
        regressor__verbose=1
    )

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_pipeline.predict(next_features)[0]

    return predicted_expense, months, y
