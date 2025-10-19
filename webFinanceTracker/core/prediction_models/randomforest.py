from core.prediction_models.base import Base
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
import numpy as np

class randomforestModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)
    
    def get_pipeline_and_grid(self):

        pipeline = Pipeline([
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
        return pipeline, param_grid
    
    def predict(self):
        if len(self.y) < 4:
            raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")
        
        y_capped = np.clip(self.y, 0, np.percentile(self.y, 95))

        pipeline, param_grid = self.get_pipeline_and_grid()
        print(f"Data size: {len(self.y)} months")
        best_params, best_mse = self.run_gridsearch(pipeline, param_grid)
        best_pipeline = Pipeline([
        ('regressor', RandomForestRegressor())
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
