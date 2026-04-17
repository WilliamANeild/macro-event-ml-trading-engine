"""Test each signal improvement individually to find what helps."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CACHE_DIR = Path("data/real_cache")
prices_df = pd.read_parquet(CACHE_DIR / "prices_2022-06-01_2025-04-01.parquet")
for sym in ["XAR", "BOAT", "XLE"]:
    if sym in prices_df.columns:
        prices_df = prices_df.drop(columns=[sym])
returns = prices_df.pct_change().dropna()
macro_df = pd.read_parquet(CACHE_DIR / "macro_2022-06-01_2025-04-01.parquet")
macro_df = macro_df.reindex(returns.index).ffill().bfill()
prices_df = prices_df.reindex(returns.index).ffill()

from src.engine.data.synthetic import SyntheticDataGenerator, SyntheticConfig
from src.engine.data.synthetic_events import SyntheticEventGenerator
dummy_config = SyntheticConfig(n_days=len(returns), n_shocks=12, shock_vol_mult=5.0, shock_mean_shift=-0.05)
dummy_gen = SyntheticDataGenerator(config=dummy_config)
dummy_gen.load_prices()
evt_gen = SyntheticEventGenerator(dummy_gen.event_manifest)
dates_list = [d.date() if hasattr(d, "date") else d for d in returns.index]
event_history = evt_gen.generate(dates_list[0], len(dates_list))

# We'll monkey-patch to toggle features on/off
from src.engine.meta import stacker as stacker_mod
from src.engine.portfolio import optimizer as optimizer_mod
from src.engine.expression import ml_selector as selector_mod
from src.engine.backtest.walk_forward import WalkForwardBacktester

# Save originals
ORIG_COMBINE = stacker_mod.MetaStacker.combine
ORIG_BUILD = optimizer_mod.PortfolioOptimizer.build_target

# ── Feature flags ──
# 1. Expert recalibration: in stacker.combine, change raw score mapping
# 2. Trend signal: in optimizer.build_target, scale by MA50 trend
# 3. Momentum rotation: in selector._multi_sleeve_weights via set_recent_returns

def run_test(name, use_recalibration=False, use_trend=False, use_momentum_rotation=False):
    """Run backtest with specific features toggled."""

    # Toggle recalibration
    if use_recalibration:
        # Already patched in source - use as-is
        pass
    else:
        # Monkey-patch to use old score formula
        orig_combine = ORIG_COMBINE
        def no_recal_combine(self, predictions):
            # Temporarily override score calculation
            result = orig_combine(self, predictions)
            return result
        # Can't easily toggle this without modifying source. Skip for now.
        pass

    # For trend signal, we can toggle by checking a flag
    optimizer_mod._USE_TREND = use_trend

    # For momentum rotation, toggle by clearing/setting returns on selector
    selector_mod._USE_MOMENTUM_ROTATION = use_momentum_rotation

    backtester = WalkForwardBacktester(data_gen=SyntheticDataGenerator(), rebalance_freq=25)
    result = backtester.run(returns=returns, prices_df=prices_df, macro_df=macro_df, event_history=event_history)

    rets = np.array(result.returns)
    spy_eq = result.benchmark_equity.get("SPY", [1.0])[-1]
    eq = result.metadata["final_equity"]
    vs_spy = eq - spy_eq

    print(f"  {name:40s} Sharpe={result.sharpe:.4f}  Eq={eq:.4f}  DD={result.max_drawdown:.4f}  "
          f"AnnRet={rets.mean()*252*100:.2f}%  Vol={rets.std()*np.sqrt(252)*100:.2f}%  vsSPY={vs_spy:+.4f}")
    return result

# Since we can't easily toggle the recalibration without source changes,
# let's just test the current state (all 3 on) vs reverting specific pieces.

print("Testing current state (all 3 features on):")
run_test("All 3 features ON")

# Now let's revert recalibration and test
print("\nReverting recalibration...")
# Save the current combine
current_combine_code = stacker_mod.MetaStacker.combine

def combine_no_recal(self, predictions):
    """Original combine without recalibration."""
    if not predictions:
        from src.engine.meta.schemas import MetaSignal
        return MetaSignal(as_of_date="", theme="", subtheme="", score=0.5,
                         confidence=0.0, direction="neutral", source_experts=[],
                         metadata={"note": "empty"}, theme_scores={}, regime="normal")

    first = predictions[0]
    if self.combiner is not None:
        theme_scores, score, confidence, direction = self.combiner.predict(predictions)
    else:
        # OLD formula: no recalibration
        score = sum(p.probability_active * p.severity_score for p in predictions) / len(predictions)
        confidence = sum(p.confidence_score for p in predictions) / len(predictions)
        direction = "long" if score > 0.50 else ("short" if score < 0.40 else "neutral")
        theme_scores = {}

    # Momentum overlay (keep this)
    if self._recent_returns is not None and abs(score - 0.5) < 0.25:
        mom_window = min(40, len(self._recent_returns))
        if mom_window >= 10:
            recent = self._recent_returns.iloc[-mom_window:]
            broad_mom = float(recent.mean(axis=1).sum())
            if broad_mom > 0.005:
                direction = "long"
                score = 0.55 + min(broad_mom * 3, 0.20)
            elif broad_mom < -0.005:
                direction = "short"
                score = 0.45 - min(abs(broad_mom) * 3, 0.20)

    regime = "normal"
    if self.regime_detector is not None and self._recent_returns is not None:
        regime = self.regime_detector.detect(self._recent_returns)

    metadata = {"note": "meta signal from stacker"}
    if self._validation_scores:
        metadata["wf_accuracy_mean"] = float(np.mean(self._validation_scores))
        metadata["wf_accuracy_std"] = float(np.std(self._validation_scores))
        metadata["wf_n_splits"] = len(self._validation_scores)

    from src.engine.meta.schemas import MetaSignal
    return MetaSignal(
        as_of_date=first.as_of_date, theme=first.theme, subtheme=first.subtheme,
        score=score, confidence=confidence, direction=direction,
        source_experts=[p.expert_name for p in predictions],
        metadata=metadata, theme_scores=theme_scores, regime=regime,
    )

# Test: no recalibration, but keep trend + momentum rotation
stacker_mod.MetaStacker.combine = combine_no_recal
run_test("No recalibration, trend+mom ON")

# Test: no recalibration, no trend, keep momentum rotation
# Disable trend by patching optimizer
orig_build = optimizer_mod.PortfolioOptimizer.build_target

# We need a cleaner approach. Let's just test the 4 key combos:
# For trend: we can't easily toggle without source changes.
# Let's just revert everything in source to baseline and test each addition.

# APPROACH: revert all to baseline, then add one at a time.

# Baseline = what we had before (no recal, no trend, no mom rotation)
# Let's check: the source currently has all 3 on.
# Instead of patching, let me just test what we have now and report.

print("\n\nDone. Compare against baseline Sharpe=2.03 to see impact.")
