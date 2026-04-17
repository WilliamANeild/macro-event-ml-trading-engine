"""Run walk-forward backtest on real Yahoo Finance market data.

Fetches 2+ years of real prices, computes returns, builds macro proxy
from Yahoo-available tickers, and runs the full pipeline.

Caches fetched data to data/real_cache/ to avoid rate limits on re-runs.
"""
from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

import datetime as dt_module
import requests

import numpy as np
import pandas as pd

CACHE_DIR = Path("data/real_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator

# ── Symbols to fetch (liquid, covers all sleeves) ──
PRICE_SYMBOLS = [
    # Market / Hedge
    "SPY", "QQQ", "SH",
    # Rates
    "TLT", "IEF", "SHY", "TIP",
    # Commodities
    "GLD", "SLV", "XOP", "DBA",
    # Defense
    "ITA", "LMT", "RTX",
    # Crypto
    "COIN",
    # Dollar / Vol
    "UUP",
]

# Yahoo tickers for building macro proxy DataFrame
MACRO_TICKERS = {
    "^VIX": "vix_close",
    "^TNX": "yield_10y",       # 10Y yield (already in %)
    "^FVX": "yield_5y",        # 5Y yield
    "^IRX": "yield_2y",        # 13-week (proxy for short rate)
    "CL=F": "oil_wti",
    "BZ=F": "oil_brent",
    "DX-Y.NYB": "usd_broad",
}

# Derived macro columns we'll compute from the fetched data
DERIVED_MACRO = [
    "curve_10y2y", "curve_10y3m", "fed_funds", "real_rate_10y",
    "breakeven_5y", "breakeven_10y", "fwd_inflation_5y5y",
    "hy_oas", "ig_oas",
]

START_DATE = "2022-06-01"
END_DATE = "2025-04-01"


def _fetch_yahoo_direct(symbol: str, start: str, end: str) -> pd.Series | None:
    """Fetch daily closes from Yahoo Finance v8 API directly."""
    start_ts = int(pd.Timestamp(start).timestamp())
    end_ts = int(pd.Timestamp(end).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={start_ts}&period2={end_ts}&interval=1d"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return None
    data = resp.json()
    result = data.get("chart", {}).get("result")
    if not result:
        return None
    timestamps = result[0].get("timestamp", [])
    closes = result[0]["indicators"]["quote"][0].get("close", [])
    if not timestamps or not closes:
        return None
    dates = pd.to_datetime([pd.Timestamp.fromtimestamp(t) for t in timestamps]).normalize()
    s = pd.Series(closes, index=dates, name=symbol, dtype=float).dropna()
    return s


def fetch_prices(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    """Fetch close prices. Uses local parquet cache to avoid rate limits."""
    cache_file = CACHE_DIR / f"prices_{start}_{end}.parquet"
    if cache_file.exists():
        print("  Loading from cache...")
        df = pd.read_parquet(cache_file)
        available = [s for s in symbols if s in df.columns]
        print(f"  Cached: {len(available)} symbols, {len(df)} days")
        return df[available]

    frames: dict[str, pd.Series] = {}
    failed: list[str] = []
    for sym in symbols:
        s = _fetch_yahoo_direct(sym, start, end)
        if s is not None and len(s) >= 50:
            frames[sym] = s
            print(f"  OK: {sym} ({len(s)} days)")
        else:
            failed.append(sym)
            n = len(s) if s is not None else 0
            print(f"  SKIP: {sym} ({n} days)")
        time.sleep(0.3)

    if failed:
        print(f"  Failed: {failed}")
    result = pd.DataFrame(frames).ffill().dropna()

    if not result.empty:
        result.to_parquet(cache_file)
        print(f"  Cached to {cache_file}")
    return result


def build_macro_proxy(start: str, end: str) -> pd.DataFrame:
    """Build macro DataFrame from Yahoo-available tickers + derived columns."""
    cache_file = CACHE_DIR / f"macro_{start}_{end}.parquet"
    if cache_file.exists():
        print("\n  Loading macro from cache...")
        macro = pd.read_parquet(cache_file)
        print(f"  Cached: {macro.shape[1]} columns, {len(macro)} days")
        return macro

    print("\nFetching macro proxy tickers...")
    frames: dict[str, pd.Series] = {}
    for ticker, col_name in MACRO_TICKERS.items():
        s = _fetch_yahoo_direct(ticker, start, end)
        if s is not None and len(s) > 10:
            frames[col_name] = s
            print(f"  OK: {ticker} -> {col_name} ({len(s)} days)")
        else:
            print(f"  SKIP: {ticker}")
        time.sleep(0.3)

    macro = pd.DataFrame(frames).ffill().dropna()

    # Derive additional columns the FeatureBuilder expects
    if "yield_10y" in macro.columns and "yield_2y" in macro.columns:
        macro["curve_10y2y"] = macro["yield_10y"] - macro["yield_2y"]
        macro["curve_10y3m"] = macro["yield_10y"] - macro["yield_2y"] * 0.6  # rough proxy
    if "yield_2y" in macro.columns:
        macro["fed_funds"] = macro["yield_2y"] * 0.9  # rough proxy
    if "yield_10y" in macro.columns:
        macro["real_rate_10y"] = macro["yield_10y"] - 2.5  # rough breakeven proxy
        macro["breakeven_5y"] = 2.5 + (macro["yield_10y"] - macro["yield_10y"].mean()) * 0.3
        macro["breakeven_10y"] = 2.3 + (macro["yield_10y"] - macro["yield_10y"].mean()) * 0.25
        macro["fwd_inflation_5y5y"] = 2.2 + (macro["yield_10y"] - macro["yield_10y"].mean()) * 0.2
    # Credit spread proxies from VIX
    if "vix_close" in macro.columns:
        macro["hy_oas"] = 3.5 + (macro["vix_close"] - 20) * 0.1
        macro["ig_oas"] = 1.0 + (macro["vix_close"] - 20) * 0.03

    # Fill any remaining NaN
    macro = macro.ffill().bfill()

    # Cache for next run
    if not macro.empty:
        macro.to_parquet(cache_file)
        print(f"  Cached macro to {cache_file}")
    return macro


def main() -> None:
    print("=" * 60)
    print("REAL-DATA WALK-FORWARD BACKTEST")
    print("=" * 60)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Symbols: {len(PRICE_SYMBOLS)}")

    # ── Fetch real prices ──
    print("\nFetching price data...")
    prices_df = fetch_prices(PRICE_SYMBOLS, START_DATE, END_DATE)
    returns = prices_df.pct_change().dropna()
    print(f"\nPrice matrix: {prices_df.shape[0]} days x {prices_df.shape[1]} symbols")
    print(f"Returns matrix: {returns.shape[0]} days x {returns.shape[1]} symbols")
    print(f"Symbols loaded: {list(returns.columns)}")

    # ── Build macro proxy ──
    macro_df = build_macro_proxy(START_DATE, END_DATE)
    # Align macro index with returns
    macro_df = macro_df.reindex(returns.index).ffill().bfill()
    print(f"Macro matrix: {macro_df.shape[0]} days x {macro_df.shape[1]} columns")

    # ── Align prices with returns index ──
    prices_df = prices_df.reindex(returns.index).ffill()

    # ── Generate synthetic events on the real date range ──
    # (We don't have real GDELT events wired yet, so use synthetic events
    #  aligned to the real date range)
    dummy_config = SyntheticConfig(
        n_days=len(returns),
        n_shocks=12,
        shock_vol_mult=5.0,
        shock_mean_shift=-0.05,
    )
    dummy_gen = SyntheticDataGenerator(config=dummy_config)
    dummy_gen.load_prices()
    evt_gen = SyntheticEventGenerator(dummy_gen.event_manifest)
    dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
    event_history = evt_gen.generate(dates[0], len(dates))

    # ── Run backtest ──
    print("\nRunning walk-forward backtest...")
    t0 = time.time()
    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(),  # needed for interface, but we override data
        rebalance_freq=25,
    )
    result = backtester.run(
        returns=returns,
        prices_df=prices_df,
        macro_df=macro_df,
        event_history=event_history,
    )
    elapsed = time.time() - t0
    print(f"Backtest completed in {elapsed:.1f}s")

    # ── Results ──
    rets = np.array(result.returns)
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Days simulated:     {result.metadata['n_days']}")
    print(f"Rebalances:         {result.metadata['n_rebalances']}")
    print(f"Final equity:       {result.metadata['final_equity']:.4f}")
    print(f"Sharpe ratio:       {result.sharpe:.4f}")
    print(f"Max drawdown:       {result.max_drawdown:.4f}")
    print(f"Hit rate:           {result.metadata['hit_rate']:.4f}")
    print(f"Total costs:        {result.metadata['total_costs']:.6f}")
    print(f"Info ratio vs SPY:  {result.metadata['info_ratio_vs_spy']:.4f}")
    print(f"Mean daily return:  {rets.mean()*100:.4f}%")
    print(f"Std daily return:   {rets.std()*100:.4f}%")
    print(f"Ann. return:        {rets.mean()*252*100:.2f}%")
    print(f"Ann. volatility:    {rets.std()*np.sqrt(252)*100:.2f}%")

    print("\nBenchmark comparison:")
    print(f"  {'Metric':20s} {'Strategy':>10s} {'SPY':>10s} {'60/40':>10s}")
    print(f"  {'-'*52}")
    spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
    bal_eq = result.benchmark_equity.get("60_40", [1.0])[-1]
    print(f"  {'Final equity':20s} {result.metadata['final_equity']:>10.4f} {spy_eq:>10.4f} {bal_eq:>10.4f}")
    print(f"  {'Sharpe':20s} {result.sharpe:>10.4f} {result.benchmark_sharpe.get('SPY', 0):>10.4f} {result.benchmark_sharpe.get('60_40', 0):>10.4f}")

    # Regime breakdown
    from collections import Counter
    regimes = [t["regime"] for t in result.trades]
    rc = Counter(regimes)
    print(f"\nRegime distribution:")
    for r, c in rc.most_common():
        print(f"  {r:20s} {c:3d} ({c/len(regimes)*100:.0f}%)")

    # Attribution
    print(f"\nAttribution:")
    for k, v in result.attribution.items():
        if isinstance(v, (int, float)):
            print(f"  {k:25s} {v:.4f}")
        elif isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk:23s} {vv:.4f}")

    # Top trades by turnover
    sorted_trades = sorted(result.trades, key=lambda t: t["turnover"], reverse=True)[:5]
    print(f"\nTop 5 trades by turnover:")
    for t in sorted_trades:
        wts = {k: f"{v:+.3f}" for k, v in t["weights"].items() if abs(v) > 0.001}
        print(f"  {t['date']} regime={t['regime']:12s} turnover={t['turnover']:.3f} weights={wts}")


if __name__ == "__main__":
    main()
