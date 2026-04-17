from __future__ import annotations

import numpy as np
import pandas as pd


class RiskEstimator:
    def __init__(self, halflife: int = 60) -> None:
        self.halflife = halflife

    def sample_covariance(self, returns: pd.DataFrame) -> np.ndarray:
        return np.array(returns.cov()) * 252

    def ewma_covariance(self, returns: pd.DataFrame) -> np.ndarray:
        ewm_cov = returns.ewm(halflife=self.halflife).cov()
        last_date = returns.index[-1]
        return np.array(ewm_cov.loc[last_date]) * 252

    def estimate(self, returns: pd.DataFrame, method: str = "ewma") -> np.ndarray:
        if method == "ewma" and len(returns) > self.halflife:
            return self.ewma_covariance(returns)
        return self.sample_covariance(returns)

    @staticmethod
    def risk_scale_weights(
        weights: np.ndarray, cov: np.ndarray, target_vol: float
    ) -> np.ndarray:
        port_var = float(weights @ cov @ weights)
        if port_var <= 0:
            return weights
        port_vol = np.sqrt(port_var)
        if port_vol < 1e-8:
            return weights
        scale = target_vol / port_vol
        return weights * scale
