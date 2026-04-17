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
    symbols: list[str] = field(default_factory=lambda: ["SPY", "TLT", "GLD", "XLE", "ITA", "SEA", "BTC-USD"])
    n_days: int = 504
    start_date: date = field(default_factory=lambda: date(2022, 1, 3))
    drift: float = 0.0002
    vol: float = 0.015
    correlation: float = 0.4
    n_shocks: int = 8
    shock_vol_mult: float = 5.0
    shock_mean_shift: float = -0.05
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
        themes = ["macro", "rates_us", "commodities", "energy", "defense", "shipping", "crypto"]
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

    def get_prices_df(self) -> pd.DataFrame:
        """Return prices as a DataFrame with DatetimeIndex and symbol columns."""
        if self._prices is None:
            self.load_prices()
        assert self._prices is not None and self._returns_df is not None
        return pd.DataFrame(self._prices, index=self._returns_df.index)

    def get_macro_df(self) -> pd.DataFrame:
        """Generate synthetic macro data matching FeatureBuilder expected columns.

        Uses a random-walk process seeded from the existing RNG for
        reproducibility.  Starting values are chosen to be realistic as of
        ~2022.
        """
        if self._returns_df is None:
            self.load_prices()
        assert self._returns_df is not None

        dates = self._returns_df.index
        n = len(dates)
        rng = np.random.default_rng(self.config.seed + 1)  # offset seed to avoid collision

        # (column_name, start_value, daily_vol)
        specs: list[tuple[str, float, float]] = [
            ("vix_close",         18.0,   0.80),
            ("yield_2y",           2.5,   0.02),
            ("yield_5y",           2.8,   0.02),
            ("yield_10y",          3.0,   0.02),
            ("curve_10y2y",        0.5,   0.01),
            ("curve_10y3m",        0.8,   0.01),
            ("fed_funds",          0.25,  0.005),
            ("real_rate_10y",      0.0,   0.01),
            ("breakeven_5y",       2.5,   0.01),
            ("breakeven_10y",      2.3,   0.01),
            ("fwd_inflation_5y5y", 2.2,   0.01),
            ("hy_oas",             4.0,   0.03),
            ("ig_oas",             1.2,   0.01),
            ("oil_wti",           80.0,   1.00),
            ("oil_brent",         85.0,   1.00),
            ("usd_broad",        100.0,   0.20),
        ]

        data: dict[str, np.ndarray] = {}
        for col, start, dvol in specs:
            shocks = rng.standard_normal(n) * dvol
            series = start + np.cumsum(shocks)
            # VIX and spreads should stay positive
            if col in ("vix_close", "hy_oas", "ig_oas", "oil_wti", "oil_brent", "usd_broad"):
                series = np.maximum(series, 0.5)
            data[col] = series

        return pd.DataFrame(data, index=dates)

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
