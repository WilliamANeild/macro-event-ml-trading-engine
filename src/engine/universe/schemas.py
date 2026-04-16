from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Instrument:
    """A tradable instrument in the macro-event universe.

    Attributes:
        symbol: Yahoo Finance compatible ticker.
        name: Human-readable instrument name.
        asset_class: e.g. equity_etf, equity_stock, commodity_etf, fixed_income_etf,
                     crypto_etf, crypto_stock, currency_etf, volatility_etp.
        theme: Top-level sleeve name (defense, shipping, commodities, crypto,
               rates_us, rates_ex_us, hedge, derivatives).
        subtheme: Sub-sleeve within the theme.
        region: Geographic region (us, global, em, europe, asia, etc.).
        tags: Free-text tags consumed by ExposureMapper TF-IDF for theme scoring.
        role: "core" for broad ETFs, "satellite" for single-name dispersion capture.
        liquidity: Approximate daily volume bucket - "high" (>5M shares/day),
                   "medium" (1-5M), "low" (<1M).
        options_available: Whether liquid listed options exist.
        futures_available: Whether exchange-traded futures exist on or closely
                          track this instrument.
        notes: Why this instrument is included in the universe.
    """

    symbol: str
    name: str
    asset_class: str
    theme: str
    subtheme: str
    region: str = "global"
    tags: list[str] = field(default_factory=list)
    role: str = "core"  # "core" or "satellite"
    liquidity: str = "medium"  # "high", "medium", "low"
    options_available: bool = False
    futures_available: bool = False
    notes: str = ""