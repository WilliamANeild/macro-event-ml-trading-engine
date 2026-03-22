from __future__ import annotations

import numpy as np
import pandas as pd


class RegimeDetector:
    def __init__(self, vol_window: int = 20, mom_window: int = 20) -> None:
        self.vol_window = vol_window
        self.mom_window = mom_window
        self._vol_mean: float = 0.0
        self._vol_std: float = 1.0
        self._mom_mean: float = 0.0
        self._mom_std: float = 1.0
        self._fitted = False

    def fit(self, returns: pd.DataFrame) -> None:
        portfolio_returns = returns.mean(axis=1)
        rolling_vol = portfolio_returns.rolling(self.vol_window).std().dropna()
        rolling_mom = portfolio_returns.rolling(self.mom_window).sum().dropna()
        self._vol_mean = float(rolling_vol.mean())
        self._vol_std = float(max(rolling_vol.std(), 1e-8))
        self._mom_mean = float(rolling_mom.mean())
        self._mom_std = float(max(rolling_mom.std(), 1e-8))
        self._fitted = True

    def detect(self, recent_returns: pd.DataFrame) -> str:
        if not self._fitted:
            return "normal"
        portfolio_returns = recent_returns.mean(axis=1)
        if len(portfolio_returns) < self.vol_window:
            return "normal"
        vol = float(portfolio_returns.iloc[-self.vol_window :].std())
        mom = float(portfolio_returns.iloc[-self.mom_window :].sum())

        vol_z = (vol - self._vol_mean) / self._vol_std
        mom_z = (mom - self._mom_mean) / self._mom_std

        if vol_z > 1.5 and mom_z < -1.0:
            return "crisis"
        if mom_z > 1.5 and vol_z < 0.5:
            return "euphoria"
        if abs(vol_z) > 1.0 or abs(mom_z) > 1.0:
            return "transition"
        return "normal"
