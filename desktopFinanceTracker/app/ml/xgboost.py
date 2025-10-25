from app.ml.base import Base
from sklearn.metrics import mean_squared_error
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
from sklearn.pipeline import Pipeline
import numpy as np
import gc, optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

class xgboost_model(Base):
    def __init__(self, user_id, n_future_months=1, pre_fetched_data=None):
        skip_fetch = pre_fetched_data is not None
        super().__init__(user_id, n_future_months, skip_fetch=skip_fetch)
        if pre_fetched_data:
            self.monthly_expenses, self.category_pivot, self.all_categories = pre_fetched_data
            self.months, self.x, self.y, self.exog = self.get_months_x_y()

        if user_id is None:
            raise ValueError("user_id must be provided")

    def prepare_data(self):
        self.fit_variance_threshold(self.x)
        x_transformed = self.variance_selector.transform(self.x)

        val_split = max(1, int(len(x_transformed) * 0.9))
        x_train, x_val = x_transformed[:val_split], x_transformed[val_split:]
        y_train, y_val = self.y[:val_split], self.y[val_split:]

        return x_train, y_train, x_val, y_val

    def objective(self, trial):
        x_train, y_train, x_val, y_val = self.prepare_data()

        params = {
            'n_estimators': 1000,
            'learning_rate': trial.suggest_float('learning_rate', 0.3, 0.5),
            'booster': trial.suggest_categorical('booster', ['gbtree', 'gblinear', 'dart']),
            'lambda': trial.suggest_float('lambda', 0.001, 5),
            'alpha': trial.suggest_float('alpha', 0.01, 25),
            'subsample': trial.suggest_float('subsample', 0.5, 1),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.5, 1),
            'max_depth': trial.suggest_int('max_depth', 4, 10),
            'n_jobs': -1,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'early_stopping_rounds': 10,
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

        if params['booster'] == 'gblinear':
            params.pop('subsample', None)
            params.pop('max_depth', None)
            params.pop('colsample_bylevel', None)
            params.pop('colsample_bytree', None)

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

    def predict(self):
        if len(self.y) < 4:
            raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

        x_train, y_train, x_val, y_val = self.prepare_data()

        sampler = TPESampler(n_startup_trials=5)
        pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=5)
        study = optuna.create_study(direction='minimize', sampler=sampler, pruner=pruner)
        study.optimize(self.objective, n_trials=160)

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

        if best_params['booster'] == 'gblinear':
            best_params.pop('subsample', None)
            best_params.pop('max_depth', None)
            best_params.pop('colsample_bylevel', None)
            best_params.pop('colsample_bytree', None)

        best_pipeline = Pipeline([
            ('scaler', scaler),
            ('regressor', xgb.XGBRegressor(**best_params, n_estimators=1000, n_jobs=-1))
        ])

        best_pipeline.fit(
            x_train, y_train,
            regressor__eval_set=[(x_val, y_val)],
            regressor__verbose=False
        )

        future_features, _ = self.generate_future_features()
        transformed_future_features = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(self.y)

        self.feature_iteration(best_pipeline, transformed_future_features, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)

        del study
        gc.collect()

        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse