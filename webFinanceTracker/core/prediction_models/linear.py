from core.prediction_models.base import Base
from django.conf import settings
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler
from sklearn.metrics import mean_squared_error
import numpy as np
import optuna, gc
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

class linearModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)

        self.scalers = {
            'standard': StandardScaler(),
            'robust': RobustScaler(),
            'minmax': MinMaxScaler(),
            'maxabs': MaxAbsScaler()
        }
        self.scaler_options = list(self.scalers.keys())

        self.regressors = {
            'linear': LinearRegression,
            'lasso': Lasso,
            'ridge': Ridge,
            'huber': HuberRegressor
        }
        self.regressor_options = list(self.regressors.keys())

    def get_storage_url(self):
        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        if engine == 'django.db.backends.sqlite3':
            db_path = db_settings['NAME']
            storage_url = f"sqlite:///{db_path}"
        elif engine == 'django.db.backends.postgresql':
            user = db_settings.get('USER')
            password = db_settings.get('PASSWORD')
            host = db_settings.get('HOST')
            port = db_settings.get('PORT')
            name = db_settings.get('NAME')
            storage_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            raise ValueError(f"Unsupported database engine: {engine}")
        
        return storage_url

    def prepare_data(self):
        self.fit_variance_threshold(self.x)
        X_transformed = self.variance_selector.transform(self.x)

        val_split = max(1, int(len(X_transformed) * 0.8))
        x_train, x_val = X_transformed[:val_split], X_transformed[val_split:]
        y_train, y_val = self.y[:val_split], self.y[val_split:]

        return x_train, y_train, x_val, y_val
    
    def objective(self, trial):
        x_train, y_train, x_val, y_val = self.prepare_data()

        regressor_choice = trial.suggest_categorical('regressor', self.regressor_options)
        regressor_class = self.regressors[regressor_choice]

        params = {
            'alpha': trial.suggest_float('alpha', 0.001, 10),
            'fit_intercept': trial.suggest_categorical('fit_intercept', [True, False]),
            'epsilon': trial.suggest_float('epsilon', 1, 2)
        }
        if regressor_choice == 'huber':
            params['max_iter'] = trial.suggest_int('max_iter', 1000, 10000)
        elif regressor_choice == 'lasso':
            params['max_iter'] = trial.suggest_int('max_iter', 1000, 10000)
            params.pop('epsilon', None)
        elif regressor_choice == 'ridge':
            params.pop('epsilon', None)
        elif regressor_choice == 'linear':
            params.pop('alpha', None)
            params.pop('epsilon', None)

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
        storage_url = self.get_storage_url()

        sampler = TPESampler(n_startup_trials=5)
        pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=5)
        study = optuna.create_study(direction='minimize', sampler=sampler, pruner=pruner, storage=storage_url)
        study.optimize(self.objective, n_trials=100)

        best_params = study.best_params
        best_mse = study.best_value
        print(f'Best paramaters: {best_params}')
        print(f'Best model MSE: {best_mse:.2f}')

        try:
            optuna.delete_study(study_name=study.study_name, storage=storage_url)
            print(f"Deleted study {study.study_name} from database")
        except Exception as e:
            print(f"Failed to delete study {study.study_name}: {str(e)}")

        regressor_choice = best_params.pop('regressor')
        if regressor_choice == 'lasso':
            best_params.pop('epsilon', None)
        elif regressor_choice == 'ridge':
            best_params.pop('epsilon', None)
        elif regressor_choice == 'linear':
            best_params.pop('alpha', None)
            best_params.pop('epsilon', None)

        scaler_choice = best_params.pop('scaler')
        regressor_class = self.regressors[regressor_choice]
        best_pipeline = Pipeline([
            ('scaler', self.scalers[scaler_choice]),
            ('regressor', regressor_class(**best_params))
        ])

        best_pipeline.fit(x_train, y_train)

        future_features, _ = self.generate_future_features()
        future_features_transformed = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(self.y)

        self.feature_iteration(best_pipeline, future_features_transformed, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)

        del study
        gc.collect()

        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse