from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.engine.features.schemas import FeatureRow
from .interfaces import BaseDataSource


@dataclass
class EventShock:
    date: date
    symbol: str
    vol_multiplier: float
    mean_shift: float
    theme: str = ""


@dataclass
class SyntheticConfig:
    symbols: list[str] = field(default_factory=lambda: ["XLE", "ITA", "SEA"])
    n_days: int = 504
    start_date: date = field(default_factory=lambda: date(2022, 1, 3))
    drift: float = 0.0002
    vol: float = 0.015
    correlation: float = 0.4
    n_shocks: int = 5
    shock_vol_mult: float = 3.0
    shock_mean_shift: float = -0.03
    seed: int = 42


class SyntheticDataGenerator(BaseDataSource):
    def __init__(self, config: SyntheticConfig | None = None) -> None:
        self.config = config or SyntheticConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self._prices: dict[str, list[float]] | None = None
        self._returns_df: pd.DataFrame | None = None
        self.event_manifest: list[EventShock] = []

    def load_prices(self, symbols: list[str] | None = None) -> dict[str, list[float]]:
        if self._prices is not None:
            return self._prices
        symbols = symbols or self.config.symbols
        cfg = self.config
        n = cfg.n_days
        k = len(symbols)

        # Build correlation matrix
        corr = np.full((k, k), cfg.correlation)
        np.fill_diagonal(corr, 1.0)
        L = np.linalg.cholesky(corr)

        # Generate correlated returns
        z = self.rng.standard_normal((n, k))
        corr_z = z @ L.T
        returns = cfg.drift + cfg.vol * corr_z

        # Generate event shocks
        self.event_manifest = []
        shock_days = sorted(self.rng.choice(range(50, n - 20), size=cfg.n_shocks, replace=False))
        themes = ["energy", "defense", "shipping"]
        for i, day_idx in enumerate(shock_days):
            sym_idx = i % k
            sym = symbols[sym_idx]
            shock_date = cfg.start_date + timedelta(days=int(day_idx))
            shock = EventShock(
                date=shock_date,
                symbol=sym,
                vol_multiplier=cfg.shock_vol_mult,
                mean_shift=cfg.shock_mean_shift,
                theme=themes[sym_idx % len(themes)],
            )
            self.event_manifest.append(shock)
            # Apply shock: 5-day window of elevated vol + mean shift
            for d in range(5):
                if day_idx + d < n:
                    returns[day_idx + d, sym_idx] += cfg.shock_mean_shift / 5
                    returns[day_idx + d, sym_idx] *= cfg.shock_vol_mult ** 0.5

        # Convert to prices
        prices_array = 100.0 * np.exp(np.cumsum(returns, axis=0))
        self._prices = {sym: prices_array[:, i].tolist() for i, sym in enumerate(symbols)}

        # Store returns DataFrame
        dates = pd.bdate_range(start=cfg.start_date, periods=n)
        self._returns_df = pd.DataFrame(returns, index=dates, columns=symbols)

        return self._prices

    def load_returns(
        self,
        symbols: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        return self.get_returns()

    def get_returns(self) -> pd.DataFrame:
        if self._returns_df is None:
            self.load_prices()
        assert self._returns_df is not None
        return self._returns_df

    def get_dates(self) -> list[date]:
        returns = self.get_returns()
        return [d.date() for d in returns.index]

    def generate_feature_history(self) -> list[FeatureRow]:
        returns = self.get_returns()
        rows: list[FeatureRow] = []
        for i in range(20, len(returns)):
            dt = returns.index[i].date()
            window = returns.iloc[i - 20 : i]
            values: dict[str, float] = {}
            for sym in returns.columns:
                values[f"{sym}_return_1d"] = float(returns.iloc[i][sym])
                values[f"{sym}_return_5d"] = float(returns.iloc[i - 5 : i][sym].sum())
                values[f"{sym}_vol_20d"] = float(window[sym].std())
                values[f"{sym}_momentum_20d"] = float(window[sym].sum())
            rows.append(FeatureRow(as_of_date=dt, theme="macro", subtheme="all", values=values))
        return rows
