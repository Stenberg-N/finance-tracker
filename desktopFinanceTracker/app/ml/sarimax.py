from app.ml.base import Base
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

class sarimax_model(Base):
    def __init__(self, user_id, n_future_months=1, pre_fetched_data=None):
        skip_fetch = pre_fetched_data is not None
        super().__init__(user_id, n_future_months, skip_fetch=skip_fetch)
        if pre_fetched_data:
            self.monthly_expenses, self.category_pivot, self.all_categories = pre_fetched_data
            self.months, self.x, self.y, self.exog = self.get_months_x_y()

        if user_id is None:
            raise ValueError("user_id must be provided")

    def predict(self):
        if len(self.y) < 12:
            raise ValueError("Insufficient data: Need at least 12 months of expenses for training.")

        def fit_sarimax(params):
            try:
                order = params['order']
                seasonal_order = params['seasonal_order']
                model = SARIMAX(self.y, exog=self.exog, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
                return -model.fit(disp=False).aic
            except Exception as e:
                print(f'Error fitting SARIMAX with params: {params}: {e}')
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

        print(f"Best score: {best_score:}")
        print(f"Best parameters: {best_params}")

        model = SARIMAX(self.y, exog=self.exog, order=best_params['order'], seasonal_order=best_params['seasonal_order'], enforce_stationarity=False, enforce_invertibility=False)
        best_model = model.fit(disp=False)

        fitted = best_model.fittedvalues
        mse = np.mean((self.y - fitted) ** 2)
        print(f"Model MSE: {mse}")

        _, future_exog = self.generate_future_features()
        predictions = best_model.forecast(steps=self.n_future_months, exog=future_exog)
        predictions = np.clip(predictions, 0, np.max(self.y) * 2)

        return predictions[0] if self.n_future_months == 1 else predictions, self.months, self.y, mse