import datetime, math
from database.db import viewAllTransactions
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.feature_selection import VarianceThreshold
from joblib import parallel_backend

class Base:
    def __init__(self, user_id, n_future_months=1, skip_fetch=False):
        self.user_id = user_id
        self.n_future_months = n_future_months
        self.variance_selector = None
        if not skip_fetch:
            self.monthly_expenses, self.category_pivot, self.all_categories = self.fetch_data()
            self.months, self.x, self.y, self.exog = self.get_months_x_y()

    def fetch_data(self):
        rows = viewAllTransactions(self.user_id)
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

    def get_months_x_y(self):
        months = sorted(self.monthly_expenses.keys())
        y = np.array([self.monthly_expenses[month] for month in months])

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

        category_features = self.category_pivot.reindex(months).fillna(0)[self.all_categories].values
        x = np.hstack([x_normalized, x_raw, rolling_mean_3m, rolling_mean_6m, month_of_year, lag1, lag12, diff1, rolling_std_3m, sin_month, cos_month, quarter, category_features])

        exog_indices = list(range(12, 12 + len(self.all_categories)))
        exog = x[:, exog_indices]

        return months, x, y, exog

    def generate_future_features(self):
        future_features = []
        last_index = len(self.months)
        last_month = datetime.datetime.strptime(self.months[-1], "%Y-%m")
        last_y = self.y[-1]
        rolling_mean_3m_base = np.mean(self.y[-3:]) if len(self.y) >= 3 else np.mean(self.y)
        rolling_mean_6m_base = np.mean(self.y[-6:]) if len(self.y) >= 6 else np.mean(self.y)
        lag1 = last_y
        lag12 = self.y[-12] if len(self.y) >= 12 else np.mean(self.y)
        diff1 = 0
        rolling_std_3m_base = pd.Series(self.y[-3:]).std() if len(self.y) >= 3 else 0

        category_history = self.category_pivot[self.all_categories].tail(12).values
        n_history = len(category_history)

        for i in range(self.n_future_months):
            next_month_raw = last_index + i
            next_month_normalized = next_month_raw / max(1, last_index)
            future_date = last_month + pd.offsets.MonthEnd(i+1)
            month_num = future_date.month
            sin_m = math.sin(2 * math.pi * month_num / 12)
            cos_m = math.cos(2 * math.pi * month_num / 12)
            quarter_val = ((month_num - 1) // 3) + 1

            category_values = category_history[i % n_history] if n_history > 0 else self.category_pivot[self.all_categories].mean().values()

            feature_row = [next_month_normalized, next_month_raw, rolling_mean_3m_base, rolling_mean_6m_base, month_num, lag1, lag12, diff1, \
                        rolling_std_3m_base, sin_m, cos_m, quarter_val] + category_values.tolist()
            future_features.append(feature_row)

        future_features = np.array(future_features, dtype=float)
        exog_indices = list(range(12, 12 + len(self.all_categories)))
        future_exog = future_features[:, exog_indices]

        return future_features, future_exog

    def fit_variance_threshold(self, x):
        self.variance_selector = VarianceThreshold(threshold=0.001)
        self.variance_selector.fit(x)
        print(f"Features after VarianceThreshold: {self.variance_selector.get_support().sum()}")
        return self.variance_selector

    def run_gridsearch(self, pipeline, param_grid):
        n_splits = max(1, min(3, (len(self.y) - 1) // 2))
        cv = TimeSeriesSplit(n_splits=n_splits)

        self.fit_variance_threshold(self.x)
        x_transformed = self.variance_selector.transform(self.x)

        gridsearch = GridSearchCV(
            pipeline,
            param_grid=param_grid,
            cv=cv,
            verbose=1,
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )

        with parallel_backend('threading'):
            gridsearch.fit(x_transformed, self.y)

        best_mse = -gridsearch.best_score_
        print(f"Best model MSE: {best_mse:.2f}")
        print(f"Best parameters: {gridsearch.best_params_}")

        return gridsearch.best_params_, best_mse, gridsearch

    def feature_iteration(self, best_pipeline, future_features, predictions, recent_y):
        for i in range(self.n_future_months):
            future_row_transformed = self.variance_selector.transform(future_features[i:i+1])
            pred = best_pipeline.predict(future_row_transformed)[0]
            pred = np.clip(pred, 0, np.max(self.y) * 2)
            predictions.append(float(pred))

            if i + 1 < self.n_future_months:
                recent_y.append(pred)
                future_features[i+1][5] = pred
                future_features[i+1][7] = pred - future_features[i][5]
                future_features[i+1][2] = np.mean(recent_y[-3:]) if len(recent_y) >= 3 else pred
                future_features[i+1][3] = np.mean(recent_y[-6:]) if len(recent_y) >= 6 else pred
                future_features[i+1][8] = pd.Series(recent_y[-3:]).std() if len(recent_y) >= 3 else 0
                if len(self.months) > 12:
                    future_features[i+1][6] = recent_y[-12] if len(recent_y) >= 12 else np.mean(recent_y)