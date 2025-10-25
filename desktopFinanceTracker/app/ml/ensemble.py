from app.ml.base import Base
from app.ml.linear import linear_model
from app.ml.polynomial import polynomial_model
from app.ml.sarimax import sarimax_model
from app.ml.xgboost import xgboost_model
import numpy as np

class ensemble_model(Base):
    def __init__(self, user_id, n_future_months=1):
        super().__init__(user_id, n_future_months)

        if user_id is None:
            raise ValueError("user_id must be provided")

    def prepare_models(self):
        pre_data = (self.monthly_expenses, self.category_pivot, self.all_categories)
        model_linear = linear_model(n_future_months=self.n_future_months, user_id=self.user_id, pre_fetched_data=pre_data)
        model_poly = polynomial_model(n_future_months=self.n_future_months, user_id=self.user_id, pre_fetched_data=pre_data)
        model_sarimax = sarimax_model(n_future_months=self.n_future_months, user_id=self.user_id, pre_fetched_data=pre_data)
        model_xgboost = xgboost_model(n_future_months=self.n_future_months, user_id=self.user_id, pre_fetched_data=pre_data)

        return model_linear, model_poly, model_sarimax, model_xgboost

    def predict(self):
        model_linear, model_poly, model_sarimax, model_xgboost = self.prepare_models()

        pred1, self.months, self.y, mse1 = model_linear.predict()
        pred2, _, _, mse2 = model_poly.predict()
        pred3, _, _, mse3 = model_sarimax.predict()
        pred4, _, _, mse4 = model_xgboost.predict()
        ensemble_pred = np.mean([pred1, pred2, pred3, pred4], axis=0) if self.n_future_months > 1 else np.mean([pred1, pred2, pred3, pred4])
        ensemble_mse = np.mean([mse1, mse2, mse3, mse4])

        return ensemble_pred, self.months, self.y, ensemble_mse