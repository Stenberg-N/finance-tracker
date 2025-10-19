from core.prediction_models.base import Base
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, HuberRegressor, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler, QuantileTransformer
import numpy as np

class linearModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)

    def get_pipeline_and_grid(self):
        pipeline = Pipeline([
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
            },
            {
                'regressor': [HuberRegressor(max_iter=10000)],
                'regressor__alpha': [0.001, 0.01, 0.1, 1, 10],
                'regressor__epsilon': [1, 1.1, 1.35, 1.5, 1.8, 2.0],
                'regressor__fit_intercept': [True, False],
                'scaler': [StandardScaler(), RobustScaler(), MinMaxScaler(), MaxAbsScaler(), QuantileTransformer()]
            }
        ]
        return pipeline, param_grid

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
                ('regressor', LinearRegression(fit_intercept=True))
            ])
            default_pipeline.fit(X_transformed, y_capped)
            best_pipeline = default_pipeline
            best_mse = None
        else:
            print(f"Data size: {len(self.y)} months")
            best_params, best_mse = self.run_gridsearch(pipeline, param_grid)
            best_pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', LinearRegression())
            ])

            best_pipeline.set_params(**best_params)
            X_transformed = self.variance_selector.transform(self.x)
            best_pipeline.fit(X_transformed, y_capped)

        future_features, _ = self.generate_future_features()
        future_features_transformed = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(y_capped)

        self.feature_iteration(best_pipeline, future_features_transformed, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)
        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse