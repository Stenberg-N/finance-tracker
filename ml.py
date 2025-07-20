from database.db import view_all_transactions
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer, PowerTransformer
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
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

def run_gridsearch(
    x, y,
    pipeline,
    param_grid,
    cv_values=[2, 3, 4],
    test_sizes=[0.1, 0.2, 0.3, 0.4]
):
    results = []
    best_score = -np.inf
    best_estimator = None
    best_test_size = None
    best_cv = None

    for test_size in test_sizes:
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=42)
        for cv in cv_values:
            gridsearch = GridSearchCV(
                pipeline,
                param_grid=param_grid,
                cv=cv,
                verbose=1,
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            gridsearch.fit(x_train, y_train)
            df = pd.DataFrame(gridsearch.cv_results_)
            df['test_size'] = test_size
            df['cv'] = cv
            results.append(df)
            if gridsearch.best_score_ > best_score:
                best_score = gridsearch.best_score_
                best_estimator = gridsearch.best_estimator_
                best_test_size = test_size
                best_cv = cv

    all_results = pd.concat(results, ignore_index=True)
    return all_results, best_estimator, best_test_size, best_cv

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
        'regressor': [Ridge(), Lasso(max_iter=1000)],
        'regressor__alpha': [0.1, 1, 10],
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()]
        }
    ]

    df, _, _, _ = run_gridsearch(x, y, pipeline_linear, param_grid)
    best_row = df.sort_values('mean_test_score', ascending=False).iloc[0]
    best_params = best_row['params']
    best_test_size = best_row['test_size']
    with pd.option_context('display.max_colwidth', None, 'display.max_rows', None):
        print("Best overall params:", best_row['params'])
        print("Best mean_test_score:", best_row['mean_test_score'])
        print("Best std_test_score:", best_row['std_test_score'])
        print("Test size:", best_row['test_size'], "CV:", best_row['cv'])

    best_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])
    best_pipeline.set_params(**best_params)

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=best_test_size, random_state=42)
    best_pipeline.fit(x_train, y_train)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = best_pipeline.predict(next_features)[0]

    return predicted_expense, months, y

def polynomial_model():
    months, x, y = get_months_x_y()
    pipeline_poly = Pipeline([
        ('scaler', StandardScaler()),
        ('poly', PolynomialFeatures()),
        ('regressor', LinearRegression()),
    ])

    param_grid = {
        'regressor__fit_intercept': [True, False],
        'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer(), PowerTransformer()],
        'poly__degree': [2, 3, 4]
    }

    df, _, _, _ = run_gridsearch(x, y, pipeline_poly, param_grid)
    best_row = df.sort_values('mean_test_score', ascending=False).iloc[0]
    best_params = best_row['params']
    best_test_size = best_row['test_size']
    with pd.option_context('display.max_colwidth', None, 'display.max_rows', None):
        print("Best overall params:", best_row['params'])
        print("Best mean_test_score:", best_row['mean_test_score'])
        print("Best std_test_score:", best_row['std_test_score'])
        print("Test size:", best_row['test_size'], "CV:", best_row['cv'])

    best_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('poly', PolynomialFeatures()),
        ('regressor', LinearRegression())
    ])
    best_pipeline.set_params(**best_params)

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=best_test_size, random_state=42)
    best_pipeline.fit(x_train, y_train)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])
    next_features = np.array([[next_month_index, next_rolling_mean]])

    predicted_expense = best_pipeline.predict (next_features)[0]

    return predicted_expense, months, y

def robust_linear_model():
    months, x, y = get_months_x_y()

    model = HuberRegressor()
    model.fit(x, y)

    next_month_index = len(months)
    next_rolling_mean = np.mean(y[-3:])

    next_features = np.array([[next_month_index, next_rolling_mean]])
    predicted_expense = model.predict (next_features)[0]

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
    ensemble_pred = np.mean([pred1, pred2, pred3])

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
