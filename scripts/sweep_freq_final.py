"""Quick sweep of rebalance freq with the final instrument set."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.backtest.metrics import compute_sharpe
from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator

CACHE_DIR = Path("data/real_cache")

prices_df = pd.read_parquet(CACHE_DIR / "prices_2022-06-01_2025-04-01.parquet")
# Drop removed instruments
for sym in ["XAR", "BOAT", "XLE"]:
    if sym in prices_df.columns:
        prices_df = prices_df.drop(columns=[sym])

returns = prices_df.pct_change().dropna()
macro_df = pd.read_parquet(CACHE_DIR / "macro_2022-06-01_2025-04-01.parquet")
macro_df = macro_df.reindex(returns.index).ffill().bfill()
prices_df = prices_df.reindex(returns.index).ffill()

dummy_config = SyntheticConfig(n_days=len(returns), n_shocks=12, shock_vol_mult=5.0, shock_mean_shift=-0.05)
dummy_gen = SyntheticDataGenerator(config=dummy_config)
dummy_gen.load_prices()
evt_gen = SyntheticEventGenerator(dummy_gen.event_manifest)
dates_list = [d.date() if hasattr(d, "date") else d for d in returns.index]
event_history = evt_gen.generate(dates_list[0], len(dates_list))

print(f"{'Freq':>5s} {'Sharpe':>8s} {'Equity':>8s} {'MaxDD':>8s} {'AnnRet':>8s} {'AnnVol':>8s} {'vsSPY':>8s} {'Trades':>7s}")
print("-" * 62)

for freq in [25, 30, 32, 35, 37, 40, 45]:
    backtester = WalkForwardBacktester(
        data_gen=SyntheticDataGenerator(), rebalance_freq=freq)
    result = backtester.run(
        returns=returns, prices_df=prices_df,
        macro_df=macro_df, event_history=event_history)

    rets = np.array(result.returns)
    spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
    eq = result.metadata["final_equity"]
    vs_spy = eq - spy_eq

    # Per-year quick check for best ones
    extra = ""
    if freq in [35, 37, 40]:
        daily_dates = [d.date() if hasattr(d, "date") else d for d in returns.index]
        for year in [2022, 2023, 2024, 2025]:
            yr = [result.returns[i] for i, d in enumerate(daily_dates)
                  if hasattr(d, 'year') and d.year == year and i < len(result.returns)]
            if yr:
                cum = float(np.prod([1+r for r in yr]) - 1)
                extra += f"  {year}:{cum*100:+.1f}%"

    print(f"{freq:>5d} {result.sharpe:>8.4f} {eq:>8.4f} {result.max_drawdown:>8.4f} "
          f"{rets.mean()*252*100:>7.2f}% {rets.std()*np.sqrt(252)*100:>7.2f}% "
          f"{vs_spy:>+8.4f} {result.metadata['n_rebalances']:>7d}{extra}")

print(f"\nSPY equity: {spy_eq:.4f}  |  60/40 equity: {result.benchmark_equity.get('60_40', [1.0])[-1]:.4f}")
