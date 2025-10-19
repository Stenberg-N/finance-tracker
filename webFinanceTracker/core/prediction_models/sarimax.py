from core.prediction_models.base import Base
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np

class sarimaxModel(Base):
    def __init__(self, transactions, n_future_months=1):
        super().__init__(transactions, n_future_months)

    def predict(self):
        if len(self.y) < 12:
            raise ValueError("Insufficient data: Need at least 12 months of expenses for SARIMAX (due to seasonality)")

        y_capped = np.clip(self.y, 0, np.percentile(self.y, 95))

        def fit_sarimax(params):
            try:
                order = params['order']
                seasonal_order = params['seasonal_order']
                model = SARIMAX(y_capped, exog=self.exog, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
                return -model.fit(disp=False).aic
            except Exception as e:
                print(f"Error fitting SARIMAX with params {params}: {e}")
                return np.inf

        param_grid = {
            'order': [(p, d, q) for p in range(3) for d in range(2) for q in range(3)],
            'seasonal_order': [(p, d, q, 12) for p in range(2) for d in range(2) for q in range(2)]
        }

        best_score = np.inf
        best_params = None
        for order in param_grid['order']:
            for seasonal_order in param_grid['seasonal_order']:
                params = {'order': order, 'seasonal_order': seasonal_order}
                score = fit_sarimax(params)
                if score < best_score:
                    best_score = score
                    best_params = params

        print(f"Best AIC: {best_score:}")
        print(f"Best parameters: {best_params}")

        model = SARIMAX(y_capped, exog=self.exog, order=best_params['order'], seasonal_order=best_params['seasonal_order'], enforce_stationarity=False, enforce_invertibility=False)
        best_model = model.fit(disp=False)

        fitted = best_model.fittedvalues
        mse = np.mean((y_capped - fitted) ** 2)
        print(f"Model MSE: {mse:.2f}")

        _, future_exog = self.generate_future_features()
        predictions = best_model.forecast(steps=self.n_future_months, exog=future_exog)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)

        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, mse