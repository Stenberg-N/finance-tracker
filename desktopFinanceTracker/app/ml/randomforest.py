from app.ml.base import Base
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np

class randomforest_model(Base):
    def __init__(self, user_id, n_future_months=1):
        super().__init__(user_id, n_future_months)

        if user_id is None:
            raise ValueError("user_id must be provided")

    def pipeline_paramgrid(self):
        pipeline = Pipeline([
            ('regressor', RandomForestRegressor())
        ])

        param_grid = [
            {
                'regressor__n_estimators': [50, 100, 150],
                'regressor__max_depth': [None, 2, 5, 8, 10],
                'regressor__min_samples_split': [2, 3],
                'regressor__min_samples_leaf': [1, 2],
                'regressor__max_features': [1.0, 'sqrt', 'log2'],
                'regressor__bootstrap': [False, True]
            }
        ]

        return pipeline, param_grid

    def predict(self):
        if len(self.y) < 4:
            raise ValueError("Insufficient data: Need at least 4 months of expenses for training.")

        pipeline, param_grid = self.pipeline_paramgrid()
        _, best_mse, gridsearch = self.run_gridsearch(pipeline, param_grid)

        best_pipeline = gridsearch.best_estimator_
        x_transformed = self.variance_selector.transform(self.x)
        best_pipeline.fit(x_transformed, self.y)

        future_features, _ = self.generate_future_features()
        transformed_future_features = self.variance_selector.transform(future_features)
        predictions = []
        recent_y = list(self.y)

        self.feature_iteration(best_pipeline, transformed_future_features, predictions, recent_y)

        predictions = np.array(predictions, dtype=float)
        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, best_mse