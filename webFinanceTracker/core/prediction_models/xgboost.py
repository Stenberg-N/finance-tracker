from core.prediction_models.base import Base
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
import numpy as np

class xgboostModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)

    def get_pipeline_and_grid(self):

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', xgb.XGBRegressor(
                objective="reg:squarederror",
                early_stopping_rounds=10,
                eval_metric="rmse"))
        ])

        param_grid = [
            {
                'regressor__n_estimators': [100, 150],
                'regressor__learning_rate': [0.1, 0.3, 0.5],
                'regressor__booster': ['gbtree', 'gblinear', 'dart'],
                'regressor__lambda': [0.001, 0.01, 0.1, 1, 10],
                'regressor__alpha': [0.001, 0.01, 0.1, 1, 10],
                'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
            }
        ]

        return pipeline, param_grid

    def run_gridsearch(self, pipeline, param_grid):
        n_splits = max(1, min(3, (len(self.y) - 1) // 2))
        tscv = TimeSeriesSplit(n_splits=n_splits)
        print(f"Data size: {len(self.y)} months, n_splits: {n_splits}")

        self.fit_variance_threshold(self.x)
        X_transformed = self.variance_selector.transform(self.x)
        print(f"Full features: {(self.x).shape[1]}, After VarianceThreshold: {X_transformed.shape[1]}")

        best_score = np.inf
        best_params = None
        
        for params in param_grid:
            for n_estimators in params['regressor__n_estimators']:
                for learning_rate in params['regressor__learning_rate']:
                    for booster in params['regressor__booster']:
                        for lambda_ in params['regressor__lambda']:
                            for alpha in params['regressor__alpha']:
                                for scaler in params['scaler']:
                                    current_params = {
                                        'scaler': scaler,
                                        'regressor__n_estimators': n_estimators,
                                        'regressor__learning_rate': learning_rate,
                                        'regressor__booster': booster,
                                        'regressor__lambda': lambda_,
                                        'regressor__alpha': alpha,
                                    }
                                    pipeline.set_params(**current_params)

                                    mse_scores = []
                                    
                                    for train_index, test_index in tscv.split(X_transformed):
                                        x_train_full, x_test = X_transformed[train_index], X_transformed[test_index]
                                        y_train_full, y_test = self.y[train_index], self.y[test_index]

                                        val_split = max(1, int(len(x_train_full) * 0.9))
                                        x_train, x_val = x_train_full[:val_split], x_train_full[val_split:]
                                        y_train, y_val = y_train_full[:val_split], y_train_full[val_split:]

                                        pipeline.fit(
                                            x_train, y_train,
                                            regressor__eval_set=[(x_val, y_val)],
                                            regressor__verbose=False
                                        )

                                        y_pred = pipeline.predict(x_test)
                                        mse = np.mean((y_test - y_pred) ** 2)
                                        mse_scores.append(mse)

                                    avg_mse = np.mean(mse_scores)
                                    if avg_mse < best_score:
                                        best_score = avg_mse
                                        best_params = current_params

        print(f"Best model MSE: {best_score:.2f}")
        print(f"Best parameters: {best_params}")

        return best_params, best_score
    
    def predict(self):
        if len(self.y) < 4:
            raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")
        
        y_capped = np.clip(self.y, 0, np.percentile(self.y, 95))

        pipeline, param_grid = self.get_pipeline_and_grid()

        if len(self.y) < 6:
            print(f"Data size: {len(self.y)} months, using fallback")
            self.fit_variance_threshold(self.x)
            X_transformed = self.variance_selector.transform(self.x)
            default_pipeline = Pipeline([
                ('scaler', RobustScaler()),
                ('regressor', xgb.XGBRegressor(
                    objective="reg:squarederror",
                    n_estimators=100,
                    learning_rate=[0.1, 0.3],
                    booster='gbtree',
                    lambda_=[0.01, 0.1, 1],
                    alpha=[0.01, 0.1, 1],
                    early_stopping_rounds=10,
                    eval_metric="rmse"))
            ])
            val_split = max(1, int(len(X_transformed) * 0.9))
            x_train, x_val = X_transformed[:val_split], X_transformed[val_split:]
            y_train, y_val = y_capped[:val_split], y_capped[val_split:]

            default_pipeline.fit(
                x_train, y_train,
                regressor__eval_set=[(x_val, y_val)],
                regressor__verbose=False
            )
            best_pipeline = default_pipeline
            best_mse = None
        else:
            best_params, best_mse = self.run_gridsearch(pipeline, param_grid)
            best_pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', xgb.XGBRegressor(
                    objective="reg:squarederror",
                    early_stopping_rounds=10,
                    eval_metric="rmse"))
            ])
            self.fit_variance_threshold(self.x)
            X_transformed = self.variance_selector.transform(self.x)

            val_split = max(1, int(len(X_transformed) * 0.9))
            x_train, x_val = X_transformed[:val_split], X_transformed[val_split:]
            y_train, y_val = y_capped[:val_split], y_capped[val_split:]

            best_pipeline.set_params(**best_params)
            best_pipeline.fit(
                x_train, y_train,
                regressor__eval_set=[(x_val, y_val)],
                regressor__verbose=False
            )

        future_features, _ = self.generate_future_features()
        future_features_transformed = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(y_capped)

        self.feature_iteration(best_pipeline, future_features_transformed, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)
        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse