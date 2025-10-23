from database.db import viewAllTransactions
import numpy as np
import datetime, math, gc, optuna
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import pandas as pd

def fetch_data(user_id):
    rows = viewAllTransactions(user_id)
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

    exog_indices = list(range(12, 12 + len(all_categories)))
    exog = x[:, exog_indices]

    return months, x, y, all_categories, exog

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

    category_history = category_pivot[all_categories].tail(12).values
    n_history = len(category_history)

    for i in range(n_future_months):
        next_month_raw = last_index + i
        next_month_normalized = next_month_raw / max(1, last_index)
        future_date = last_month + pd.offsets.MonthEnd(i+1)
        month_num = future_date.month
        sin_m = math.sin(2 * math.pi * month_num / 12)
        cos_m = math.cos(2 * math.pi * month_num / 12)
        quarter_val = ((month_num - 1) // 3) + 1

        category_values = category_history[i % n_history] if n_history > 0 else category_pivot[all_categories].mean().values()

        feature_row = [next_month_normalized, next_month_raw, rolling_mean_3m_base, rolling_mean_6m_base, month_num, lag1, lag12, diff1, \
                      rolling_std_3m_base, sin_m, cos_m, quarter_val] + category_values.tolist()
        future_features.append(feature_row)

    future_features = np.array(future_features, dtype=float)
    exog_indices = list(range(12, 12 + len(all_categories)))
    future_exog = future_features[:, exog_indices]

    return future_features, future_exog

def fit_variance_threshold(x):
    variance_selector = VarianceThreshold(threshold=0.001)
    variance_selector.fit(x)
    print(f"Features after VarianceThreshold: {variance_selector.get_support().sum()}")
    return variance_selector

def run_gridsearch(x, y, pipeline, param_grid):
    n_splits = max(1, min(3, (len(y) - 1) // 2))
    cv = TimeSeriesSplit(n_splits=n_splits)

    gridsearch = GridSearchCV(
        pipeline,
        param_grid=param_grid,
        cv=cv,
        verbose=1,
        scoring='neg_mean_squared_error',
        n_jobs=-1
    )

    gridsearch.fit(x, y)

    best_mse = -gridsearch.best_score_
    print(f"Best model MSE: {best_mse:.2f}")
    print(f"Best parameters: {gridsearch.best_params_}")

    return gridsearch.best_params_, best_mse, gridsearch

def feature_iteration(n_future_months, best_pipeline, future_features, variance_selector, predictions, recent_y, y, months):
    for i in range(n_future_months):
        future_row_transformed = variance_selector.transform(future_features[i:i+1])
        pred = best_pipeline.predict(future_row_transformed)[0]
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

def linear_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories, _ = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

    if len(y) < 4:
        raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

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
            'regressor__alpha': [0.001, 0.01, 0.1, 1, 10],
            'regressor__fit_intercept': [True, False],
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
        }
    ]

    variance_selector = fit_variance_threshold(x)
    x_transformed = variance_selector.transform(x)

    _, best_mse, gridsearch = run_gridsearch(x_transformed, y, pipeline_linear, param_grid)

    best_pipeline = gridsearch.best_estimator_
    best_pipeline.fit(x_transformed, y)

    future_features, _ = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = []
    recent_y = list(y)

    feature_iteration(n_future_months, best_pipeline, future_features, variance_selector, predictions, recent_y, y, months)

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y, best_mse

def polynomial_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories, _ = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

    if len(y) < 4:
        raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

    pipeline_poly = Pipeline([
        ('poly', PolynomialFeatures()),
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression()),
    ])

    param_grid = [
        {
            'regressor': [Ridge(), Lasso(max_iter=10000)],
            'regressor__alpha': [0.001, 0.01, 0.1, 1, 10],
            'regressor__fit_intercept': [True, False],
            'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()],
            'poly__degree': [2, 3]
        }
    ]

    variance_selector = fit_variance_threshold(x)
    x_transformed = variance_selector.transform(x)

    _, best_mse, gridsearch = run_gridsearch(x_transformed, y, pipeline_poly, param_grid)

    best_pipeline = gridsearch.best_estimator_
    best_pipeline.fit(x_transformed, y)

    future_features, _ = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = []
    recent_y = list(y)

    feature_iteration(n_future_months, best_pipeline, future_features, variance_selector, predictions, recent_y, y, months)

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y, best_mse

def sarimax_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories, exog = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

    if len(y) < 12:
        raise ValueError("Insufficient data: Need at least 12 months of expenses for training.")

    y_capped = np.clip(y, 0, np.percentile(y, 99))

    def fit_sarimax(params):
        try:
            order = params['order']
            seasonal_order = params['seasonal_order']
            model = SARIMAX(y_capped, exog=exog, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
            return -model.fit(disp=False).aic
        except Exception as e:
            print(f'Error fitting SARIMAX with params: {params}: {e}')
            return np.inf

    param_grid = {
        'order': [(p, d, q) for p in range(3) for d in range(2) for q in range(3)],
        'seasonal_order': [(p, d, q, 12) for p in range(2) for d in range(2) for q in range(2)]
    }

    best_score = np.inf
    best_params = None
    for order in param_grid['order']:
        for seasonal_order in param_grid['seasonal_order']:
            params = {'order': order, 'seasonal_order': seasonal_order}
            score = fit_sarimax(params)
            if score < best_score:
                best_score = score
                best_params = params

    print(f"Best score: {best_score:}")
    print(f"Best parameters: {best_params}")

    model = SARIMAX(y_capped, exog=exog, order=best_params['order'], seasonal_order=best_params['seasonal_order'], enforce_stationarity=False, enforce_invertibility=False)
    best_model = model.fit(disp=False)

    fitted = best_model.fittedvalues
    mse = np.mean((y_capped - fitted) ** 2)
    print(f"Model MSE: {mse:.2f}")

    _, future_exog = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = best_model.forecast(steps=n_future_months, exog=future_exog)
    predictions = np.clip(predictions, 0, np.max(y) * 2)

    return predictions[0] if n_future_months == 1 else predictions, months, y, mse

def randomforest_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories, _ = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

    if len(y) < 4:
        raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

    pipeline_randomforest = Pipeline([
        ('regressor', RandomForestRegressor())
    ])

    param_grid = {
        'regressor__n_estimators': [50, 100, 150],
        'regressor__max_depth': [None, 2, 5, 8, 10],
        'regressor__min_samples_split': [2, 3],
        'regressor__min_samples_leaf': [1, 2],
        'regressor__max_features': [1.0, 'sqrt', 'log2'],
        'regressor__bootstrap': [False, True]
    }

    variance_selector = fit_variance_threshold(x)
    x_transformed = variance_selector.transform(x)

    _, best_mse, gridsearch = run_gridsearch(x_transformed, y, pipeline_randomforest, param_grid)

    best_pipeline = gridsearch.best_estimator_
    best_pipeline.fit(x_transformed, y)

    future_features, _ = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = []
    recent_y = list(y)

    feature_iteration(n_future_months, best_pipeline, future_features, variance_selector, predictions, recent_y, y, months)

    predictions = np.array(predictions, dtype=float)
    return predictions[0] if n_future_months == 1 else predictions, months, y, best_mse

def xgboost_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    months, x, y, all_categories, _ = get_months_x_y(user_id)
    _, category_pivot, _ = fetch_data(user_id)

    if len(y) < 4:
        raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

    variance_selector = fit_variance_threshold(x)
    x_transformed = variance_selector.transform(x)

    val_split = max(1, int(len(x_transformed) * 0.9))
    x_train, x_val = x_transformed[:val_split], x_transformed[val_split:]
    y_train, y_val = y[:val_split], y[val_split:]

    def objective(trial):
        params = {
            'n_estimators': 1000,
            'learning_rate': trial.suggest_float('learning_rate', 0.1, 0.5, log=True),
            'booster': trial.suggest_categorical('booster', ['gbtree', 'gblinear', 'dart']),
            'lambda': trial.suggest_float('lambda', 0.001, 10, log=True),
            'alpha': trial.suggest_float('alpha', 0.001, 100, log=True),
            'subsample': trial.suggest_float('subsample', 0.1, 1),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.5, 1),
            'max_depth': trial.suggest_int('max_depth', 2, 10),
            'n_jobs': -1,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'early_stopping_rounds': 20,
            'verbosity': 0
        }
        scaler_choice = trial.suggest_categorical('scaler', ['standard', 'robust', 'minmax', 'maxabs', 'quantile'])
        if scaler_choice == 'standard':
            scaler = StandardScaler()
        elif scaler_choice == 'robust':
            scaler = RobustScaler()
        elif scaler_choice == 'minmax':
            scaler = MinMaxScaler()
        elif scaler_choice == 'maxabs':
            scaler = MaxAbsScaler()
        else:
            scaler = QuantileTransformer()

        pipeline = Pipeline([
            ('scaler', scaler),
            ('regressor', xgb.XGBRegressor(**params))
        ])
        pipeline.fit(
            x_train, y_train,
            regressor__eval_set=[(x_val, y_val)],
            regressor__verbose=False
        )

        predictions = pipeline.predict(x_val)
        return mean_squared_error(y_val, predictions)

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=250)

    best_params= study.best_params
    best_mse = study.best_value
    print(f'Best parameters: {best_params}')
    print(f'Best model MSE: {best_mse:.2f}')

    scaler_choice = best_params.pop('scaler')
    if scaler_choice == 'standard':
        scaler = StandardScaler()
    elif scaler_choice == 'robust':
        scaler = RobustScaler()
    elif scaler_choice == 'minmax':
        scaler = MinMaxScaler()
    elif scaler_choice == 'maxabs':
        scaler = MaxAbsScaler()
    else:
        scaler = QuantileTransformer()

    best_pipeline = Pipeline([
        ('scaler', scaler),
        ('regressor', xgb.XGBRegressor(**best_params, n_estimators=1000, n_jobs=-1))
    ])

    best_pipeline.fit(
        x_train, y_train,
        regressor__eval_set=[(x_val, y_val)],
        regressor__verbose=False
    )

    future_features, _ = generate_future_features(months, y, n_future_months, category_pivot, all_categories)
    predictions = []
    recent_y = list(y)

    feature_iteration(n_future_months, best_pipeline, future_features, variance_selector, predictions, recent_y, y, months)

    predictions = np.array(predictions, dtype=float)

    del study
    gc.collect()

    return predictions[0] if n_future_months == 1 else predictions, months, y, best_mse

def ensemble_model(n_future_months=1, user_id=None):
    if user_id is None:
        raise ValueError("user_id must be provided")

    pred1, months, y, mse1 = linear_model(n_future_months, user_id)
    pred2, _, _, mse2 = polynomial_model(n_future_months, user_id)
    pred3, _, _, mse3 = sarimax_model(n_future_months, user_id)
    pred4, _, _, mse4 = xgboost_model(n_future_months, user_id)
    ensemble_pred = np.mean([pred1, pred2, pred3, pred4], axis=0) if n_future_months > 1 else np.mean([pred1, pred2, pred3, pred4])
    ensemble_mse = np.mean([mse1, mse2, mse3, mse4])

    return ensemble_pred, months, y, ensemble_mse