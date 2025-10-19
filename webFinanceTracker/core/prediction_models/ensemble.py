from core.prediction_models.base import Base
from core.prediction_models.linear import linearModel
from core.prediction_models.polynomial import polynomialModel
from core.prediction_models.sarimax import sarimaxModel
from core.prediction_models.xgboost import xgboostModel
import numpy as np

class ensembleModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)

    def predict(self):
        if len(self.y) < 12:
            raise ValueError("Insufficient data: Need at least 12 months of expenses for ensemble (due to SARIMAX seasonality)")
        
        models = [
            linearModel(self.transactions, self.n_future_months),
            polynomialModel(self.transactions, self.n_future_months),
            sarimaxModel(self.transactions, self.n_future_months),
            xgboostModel(self.transactions, self.n_future_months)
        ]

        predictions_list = []
        mse_list = []
        months = None
        y = None

        for model in models:
            try:
                result = model.predict()
                if self.n_future_months == 1:
                    predictions_list.append(result)
                else:
                    pred, model_months, model_y, mse = result
                    predictions_list.append(pred)
                    mse_list.append(mse)
                    if months is None:
                        months = model_months
                        y = model_y
            except Exception as e:
                print(f"Error in {model.__class__.__name__}: {e}")
                predictions_list.append(np.nan)
                mse_list.append(np.nan)

        valid_predictions = [p for p in predictions_list if not np.any(np.isnan(p))]
        valid_mses = [m for m in mse_list if not np.isnan(m)]

        if not valid_predictions:
            raise ValueError("All models failed to generate predictions.")
        
        weights = [1/mse if mse > 0 else 0 for mse in valid_mses]
        weights = np.array(weights) / np.sum(weights)
        ensemble_pred = np.mean(valid_predictions, axis=0, weights=weights) if self.n_future_months > 1 else np.mean(valid_predictions)
        ensemble_mse = np.mean(valid_mses) if valid_mses else None

        return ensemble_pred if self.n_future_months == 1 else (ensemble_pred, months, y, ensemble_mse)