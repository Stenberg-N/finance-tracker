from database.db import view_all_transactions
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
import xgboost as xgb
from itertools import product
import pandas as pd
import math

def fetch_data(user_id):
    rows = view_all_transactions(user_id)
    data = []

    for row in rows:
        date = row[1]
        amount = row[4]
        type_ = row[5]
        category = row[2]
        if type_ == "expense":
            date_obj = datetime.datetime.strptime(date, "%d-%m-%Y")
            month_key = date_obj.strftime("%Y-%m")
            data.append({"YearMonth": month_key, "Category": category, "Amount": abs(amount)})

    df = pd.DataFrame(data)
    monthly_expenses = df.groupby("YearMonth")["Amount"].sum().to_dict()

    all_categories = sorted(df["Category"].unique())
    category_pivot = df.pivot_table(index="YearMonth", columns="Category", values="Amount", aggfunc="sum", fill_value=0)

    for cat in all_categories:
        if cat not in category_pivot.columns:
            category_pivot[cat] = 0

    return monthly_expenses, category_pivot, all_categories

def get_months_x_y(user_id):
    monthly_expenses, category_pivot, all_categories = fetch_data(user_id)
    months = sorted(monthly_expenses.keys())
    y = np.array([monthly_expenses[month] for month in months])

    x_raw = np.arange(len(months)).reshape(-1, 1)
    x_normalized = x_raw / max(1, len(months) - 1)
    rolling_mean_3m = pd.Series(y).rolling(window=3, center=True).mean().bfill().ffill().values.reshape(-1, 1)
    rolling_mean_6m = pd.Series(y).rolling(window=6, center=True).mean().bfill().ffill().values.reshape(-1, 1)
    month_of_year = np.array([int(month.split("-")[1]) for month in months]).reshape(-1, 1)
    lag1 = np.roll(y, 1).reshape(-1, 1)
    lag1[0] = y[0]
    lag12 = np.roll(y, 12).reshape(-1, 1)
    lag12[:12] = np.mean(y[:12])
    diff1 = np.diff(y, prepend=y[0]).reshape(-1, 1)
    rolling_std_3m = pd.Series(y).rolling(window=3, center=True).std().bfill().ffill().values.reshape(-1, 1)
    sin_month = np.sin(2 * np.pi * month_of_year / 12)
    cos_month = np.cos(2 * np.pi * month_of_year / 12)
    quarter = ((month_of_year - 1) // 3 + 1).reshape(-1, 1)

    category_features = category_pivot.reindex(months).fillna(0)[all_categories].values
    x = np.hstack([x_normalized, x_raw, rolling_mean_3m, rolling_mean_6m, month_of_year, lag1, lag12, diff1, rolling_std_3m, sin_month, cos_month, quarter, category_features])

    return months, x, y, all_categories

def generate_future_features(months, y, n_future_months, category_pivot, all_categories):
    future_features = []
    last_index = len(months)
    last_month = datetime.datetime.strptime(months[-1], "%Y-%m")
    last_y = y[-1]
    rolling_mean_3m_base = np.mean(y[-3:]) if len(y) >= 3 else np.mean(y)
    rolling_mean_6m_base = np.mean(y[-6:]) if len(y) >= 6 else np.mean(y)
    lag1 = last_y
    lag12 = y[-12] if len(y) >= 12 else np.mean(y)
    diff1 = 0
    rolling_std_3m_base = pd.Series(y[-3:]).std() if len(y) >= 3 else 0

    avg_category = category_pivot[all_categories].mean().values.reshape(-1, 1)

    for i in range(n_future_months):
        next_month_raw = last_index + i
        next_month_normalized = next_month_raw / max(1, last_index)
        future_date = last_month + pd.offsets.MonthEnd(i+1)
        month_num = future_date.month
        sin_m = math.sin(2 * math.pi * month_num / 12)
        cos_m = math.cos(2 * math.pi * month_num / 12)
        quarter_val = ((month_num - 1) // 3) + 1

        feature_row = [next_month_normalized, next_month_raw, rolling_mean_3m_base, rolling_mean_6m_base, month_num, lag1, lag12, diff1, \
                      rolling_std_3m_base, sin_m, cos_m, quarter_val] + avg_category.flatten().tolist()
        future_features.append(feature_row)

    future_features = np.array(future_features, dtype=float)

    return future_features

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

def linear_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

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
            'regressor__alpha': [0.01, 0.1, 1, 10, 100, 1000],
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

    future_features = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = []
    recent_y = list(y)

    for i in range(n_future_months):
        pred = best_pipeline.predict(future_features[i:i+1])[0]
        pred = np.clip(pred, 0, np.max(y) * 2)
        predictions.append(float(pred))

        if i + 1 < n_future_months:
            recent_y.append(pred)
            future_features[i+1][5] = pred
            future_features[i+1][7] = pred - future_features[i][5]
            future_features[i+1][2] = np.mean(recent_y[-3:]) if len(recent_y) >= 3 else pred
            future_features[i+1][3] = np.mean(recent_y[-6:]) if len(recent_y) >= 6 else pred
            future_features[i+1][8] = pd.Series(recent_y[-3:]).std() if len(recent_y) >= 3 else 0
            if len(months) > 12:
                future_features[i+1][6] = recent_y[-12] if len(recent_y) >= 12 else np.mean(recent_y)

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y

def polynomial_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y = get_months_x_y(user_id)

    pipeline_poly = Pipeline([
        ('poly', PolynomialFeatures()),
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression()),
    ])

    param_grid = [
        {
            'regressor': [Ridge(), Lasso(max_iter=10000)],
            'regressor__alpha': [0.01, 0.1, 1, 10, 100, 1000],
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

    future_features = generate_future_features(months, y, n_future_months)
    predictions = []

    for i in range(n_future_months):
        pred = best_pipeline.predict(future_features[i:i+1])[0]
        pred = np.clip(pred, 0, np.max(y) * 2)
        predictions.append(float(pred))

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y

def sarimax_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y = get_months_x_y(user_id)

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

    future_features = generate_future_features(months, y, n_future_months)
    predictions = best_model.forecast(steps=n_future_months, exog=future_features)
    predictions = np.clip(predictions, 0, max(y) * 2)

    return predictions[0] if n_future_months == 1 else predictions, months, y

def randomforest_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y = get_months_x_y(user_id)

    pipeline_randomforest = Pipeline([
        ('regressor', RandomForestRegressor())
    ])

    param_grid = {
        'regressor__n_estimators': [100, 200],
        'regressor__max_depth': [None, 2, 5],
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

    future_features = generate_future_features(months, y, n_future_months)
    predictions = []

    for i in range(n_future_months):
        pred = best_pipeline.predict(future_features[i:i+1])[0]
        pred = np.clip(pred, 0, np.max(y) * 2)
        predictions.append(float(pred))

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y

def xgboost_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y = get_months_x_y(user_id)

    pipeline_xgb = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', xgb.XGBRegressor(
            objective="reg:squarederror",
            early_stopping_rounds=10,
            eval_metric="rmse"))
    ])

    param_grid = {
        'regressor__n_estimators': [50, 100, 150, 200],
        'regressor__learning_rate': [0.01, 0.1, 0.3],
        'regressor__booster': ['gbtree', 'gblinear', 'dart'],
        'regressor__lambda': [0.01, 0.1, 0, 1, 5, 10, 100],
        'regressor__alpha': [0.01, 0.1, 0, 1, 5, 10],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
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
            regressor__verbose=False
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
        regressor__verbose=False
    )

    future_features = generate_future_features(months, y, n_future_months)
    predictions = []

    for i in range(n_future_months):
        pred = best_pipeline.predict(future_features[i:i+1])[0]
        pred = np.clip(pred, 0, np.max(y) * 2)
        predictions.append(float(pred))

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y

def ensemble_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    pred1, months, y = linear_model(n_future_months, user_id)
    pred2, _, _ = randomforest_model(n_future_months, user_id)
    pred3, _, _ = sarimax_model(n_future_months, user_id)
    pred4, _, _ = xgboost_model(n_future_months, user_id)
    ensemble_pred = np.mean([pred1, pred2, pred3, pred4], axis=0) if n_future_months > 1 else np.mean([pred1, pred2, pred3, pred4])

    return ensemble_pred, months, y