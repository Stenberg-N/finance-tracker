from app.ml.base import Base
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
from sklearn.metrics import mean_squared_error
import numpy as np
import optuna, gc
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

class linear_model(Base):
    def __init__(self, user_id, n_future_months=1, pre_fetched_data=None):
        skip_fetch = pre_fetched_data is not None
        super().__init__(user_id, n_future_months, skip_fetch=skip_fetch)
        if pre_fetched_data:
            self.monthly_expenses, self.category_pivot, self.all_categories = pre_fetched_data
            self.months, self.x, self.y, self.exog = self.get_months_x_y()

        if user_id is None:
            raise ValueError("user_id must be provided")
        
        self.scalers = {
            'standard': StandardScaler(),
            'robust': RobustScaler(),
            'minmax': MinMaxScaler(),
            'maxabs': MaxAbsScaler(),
            'quantile': QuantileTransformer()
        }
        self.scaler_options = list(self.scalers.keys())

        self.regressors = {
            'linear': LinearRegression,
            'lasso': Lasso,
            'ridge': Ridge
        }
        self.regressor_options = list(self.regressors.keys())

    def prepare_data(self):
        self.fit_variance_threshold(self.x)
        x_transformed = self.variance_selector.transform(self.x)

        val_split = max(1, int(len(x_transformed) * 0.8))
        x_train, x_val = x_transformed[:val_split], x_transformed[val_split:]
        y_train, y_val = self.y[:val_split], self.y[val_split:]

        return x_train, y_train, x_val, y_val

    def objective(self, trial):
        x_train, y_train, x_val, y_val = self.prepare_data()

        regressor_choice = trial.suggest_categorical('regressor', self.regressor_options)
        regressor_class = self.regressors[regressor_choice]

        params = {
            'alpha': trial.suggest_float('alpha', 0.001, 10),
            'fit_intercept': trial.suggest_categorical('fit_intercept', [True, False]),
        }
        if regressor_choice == 'lasso':
            params['max_iter'] = trial.suggest_int('max_iter', 1000, 10000)
        elif regressor_choice == 'linear':
            params.pop('alpha', None)

        pipeline = Pipeline([
            ('scaler', self.scalers[trial.suggest_categorical('scaler', self.scaler_options)]),
            ('regressor', regressor_class(**params))
        ])
        pipeline.fit(x_train, y_train)

        predictions = pipeline.predict(x_val)
        return mean_squared_error(y_val, predictions)

    def predict(self):
        if len(self.y) < 4:
            raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

        x_train, y_train, _, _ = self.prepare_data()

        sampler = TPESampler(n_startup_trials=5)
        pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=5)
        study = optuna.create_study(direction='minimize', sampler=sampler, pruner=pruner)
        study.optimize(self.objective, n_trials=100)

        best_params = study.best_params
        best_mse = study.best_value
        print(f'Best parameters: {best_params}')
        print(f'Best model MSE: {best_mse}')

        regressor_choice = best_params.pop('regressor')
        if regressor_choice == 'linear':
            best_params.pop('alpha', None)

        scaler_choice = best_params.pop('scaler')
        regressor_class = self.regressors[regressor_choice]
        best_pipeline = Pipeline([
            ('scaler', self.scalers[scaler_choice]),
            ('regressor', regressor_class(**best_params))
        ])

        best_pipeline.fit(x_train, y_train)

        future_features, _ = self.generate_future_features()
        transformed_future_features = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(self.y)

        self.feature_iteration(best_pipeline, transformed_future_features, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)

        del study
        gc.collect()

        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse
