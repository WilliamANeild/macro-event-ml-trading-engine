from __future__ import annotations

import argparse
import os
import sys
from datetime import date

import pandas as pd

from src.engine.backtest.engine import BacktestEngine
from src.engine.data.loader import MockDataSource
from src.engine.derivatives.overlay import DerivativesOverlayManager
from src.engine.events.builder import EventFeatureBuilder
from src.engine.experts.registry import get_experts
from src.engine.experts.schemas import ExpertContext
from src.engine.features.builder import FeatureBuilder
from src.engine.meta.stacker import MetaStacker
from src.engine.portfolio.optimizer import PortfolioOptimizer
from src.engine.universe.registry import get_universe


def run_mock() -> None:
    print("stage 0: load universe")
    universe = get_universe()
    symbols = [instrument.symbol for instrument in universe]
    print(f"loaded {len(symbols)} instruments")

    print("stage 1: load prices")
    data_source = MockDataSource()
    prices = data_source.load_prices(symbols)
    print(f"loaded prices for {len(prices)} symbols")

    print("stage 2: build features")
    as_of_date = date.today()
    feature_builder = FeatureBuilder()
    prices_df, returns_df = FeatureBuilder.from_dict(prices)
    # Add a DatetimeIndex so weekly resampling works
    prices_df.index = pd.bdate_range(end=as_of_date, periods=len(prices_df))
    returns_df.index = pd.bdate_range(end=as_of_date, periods=len(returns_df))
    macro_df = pd.DataFrame(index=prices_df.index)  # empty macro for mock mode
    feature_row = feature_builder.build(
        as_of_date=as_of_date,
        theme="shipping",
        subtheme="suez",
        prices=prices_df,
        returns=returns_df,
        macro=macro_df,
    )
    print(f"built {len(feature_row.values)} features")

    print("stage 3: build event features")
    event_builder = EventFeatureBuilder()
    event_row = event_builder.build(
        as_of_date=as_of_date,
        theme="shipping",
        subtheme="suez",
        region="mena",
    )
    print(f"built {len(event_row.values)} event features")

    print("stage 4: build expert context")
    context = ExpertContext(
        as_of_date=feature_row.as_of_date,
        theme=feature_row.theme,
        subtheme=feature_row.subtheme,
        feature_row=feature_row.values,
        event_features=event_row.values,
        universe=symbols,
    )

    print("stage 5: load experts")
    experts = get_experts()

    print("stage 6: run experts")
    predictions = []
    for expert in experts:
        prediction = expert.predict(context)
        predictions.append(prediction)
        print(f"{expert.expert_name} -> {prediction}")

    print("stage 7: combine meta signal")
    stacker = MetaStacker()
    meta_signal = stacker.combine(predictions)
    print(meta_signal)

    print("stage 8: select expression")
    from src.engine.expression.selector import ExpressionSelector
    selector = ExpressionSelector()
    expression_decision = selector.select(meta_signal)
    print(expression_decision)

    print("stage 9: build portfolio target")
    optimizer = PortfolioOptimizer()
    portfolio_target = optimizer.build_target(expression_decision)
    print(portfolio_target)

    print("stage 10: build derivatives overlay")
    overlay_manager = DerivativesOverlayManager()
    overlay = overlay_manager.build_overlay(meta_signal, portfolio_target)
    print(overlay)

    print("stage 11: run backtest")
    backtest_engine = BacktestEngine()
    backtest_result = backtest_engine.run(portfolio_target, overlay)
    print(backtest_result)

    print("stage 12: pipeline complete")


def run_full() -> None:
    from src.engine.data.synthetic import SyntheticDataGenerator
    from src.engine.data.synthetic_events import SyntheticEventGenerator
    from src.engine.expression.ml_selector import MLExpressionSelector

    print("stage 0: load universe")
    universe = get_universe()
    symbols = [inst.symbol for inst in universe]
    print(f"loaded {len(symbols)} instruments")

    print("stage 1: generate synthetic data")
    data_gen = SyntheticDataGenerator()
    data_gen.load_prices(symbols)
    returns = data_gen.get_returns()
    prices_df = data_gen.get_prices_df()
    macro_df = data_gen.get_macro_df()
    print(f"generated {len(returns)} days of synthetic data")

    print("stage 2: build feature history")
    feature_builder = FeatureBuilder()
    features = []
    for i in range(20, len(returns)):
        dt = returns.index[i].date()
        feat = feature_builder.build(
            as_of_date=dt,
            theme="macro",
            subtheme="all",
            prices=prices_df.iloc[:i + 1],
            returns=returns.iloc[:i + 1],
            macro=macro_df.iloc[:i + 1],
        )
        features.append(feat)
    print(f"built {len(features)} feature rows")

    print("stage 3: generate event history")
    evt_gen = SyntheticEventGenerator(data_gen.event_manifest)
    dates = data_gen.get_dates()
    events = evt_gen.generate(dates[0], len(dates))
    print(f"generated {len(events)} event rows")

    # Use latest feature/event for single-step pipeline demo
    feat = features[-1]
    evt = events[-1]

    print("stage 4: build expert context")
    context = ExpertContext(
        as_of_date=feat.as_of_date,
        theme="macro",
        subtheme="all",
        feature_row=feat.values,
        event_features=evt.values,
        universe=symbols,
    )

    print("stage 5: run experts")
    experts = get_experts()
    predictions = [expert.predict(context) for expert in experts]
    for p in predictions:
        print(f"  {p.expert_name} -> score={p.probability_active:.3f}")

    print("stage 6: combine meta signal")
    stacker = MetaStacker()
    stacker.set_recent_returns(returns)
    meta_signal = stacker.combine(predictions)
    print(f"  score={meta_signal.score:.3f} conf={meta_signal.confidence:.3f} regime={meta_signal.regime}")

    print("stage 7: select expression (ML)")
    selector = MLExpressionSelector(universe=universe)
    expression = selector.select(meta_signal)
    print(f"  type={expression.expression_type} symbols={expression.target_symbols}")

    print("stage 8: optimize portfolio")
    optimizer = PortfolioOptimizer(returns=returns, universe=universe)
    portfolio = optimizer.build_target(expression, regime=meta_signal.regime, signal_score=meta_signal.score)
    print(f"  weights={portfolio.weights} gross={portfolio.gross_exposure:.4f}")

    print("stage 9: build derivatives overlay")
    overlay_mgr = DerivativesOverlayManager()
    overlay = overlay_mgr.build_overlay(meta_signal, portfolio)
    print(f"  type={overlay.overlay_type} structure={overlay.structure}")

    print("stage 10: pipeline complete")


def run_live() -> None:
    from src.engine.data.yahoo_loader import YahooDataSource
    from src.engine.expression.ml_selector import MLExpressionSelector

    print("stage 0: load universe")
    universe = get_universe()
    symbols = [inst.symbol for inst in universe]
    print(f"loaded {len(symbols)} instruments")

    print("stage 1: load live market data (Yahoo Finance)")
    yahoo = YahooDataSource()
    prices_df = yahoo.load_prices(symbols, start="2023-01-01")
    returns = prices_df.pct_change().dropna()
    print(f"loaded {len(returns)} days of returns for {list(returns.columns)}")

    print("stage 1b: load macro data (FRED)")
    try:
        from src.engine.data.fred_loader import FREDDataSource
        fred = FREDDataSource()
        macro_df = fred.load_macro(start="2023-01-01")
        # Align macro index with prices index
        macro_df = macro_df.reindex(prices_df.index).ffill().fillna(0.0)
    except Exception as e:
        print(f"  FRED unavailable ({e}), using empty macro DataFrame")
        macro_df = pd.DataFrame(index=prices_df.index)

    print("stage 2: build features via FeatureBuilder")
    as_of_date = returns.index[-1].date()
    feature_builder = FeatureBuilder()
    feature_row = feature_builder.build(
        as_of_date=as_of_date,
        theme="macro",
        subtheme="all",
        prices=prices_df,
        returns=returns,
        macro=macro_df,
    )

    print(f"  built {len(feature_row.values)} features")

    print("stage 2b: build expert context")
    context = ExpertContext(
        as_of_date=as_of_date,
        theme="macro",
        subtheme="all",
        feature_row=feature_row.values,
        event_features={},
        universe=symbols,
    )

    print("stage 3: run experts")
    experts = get_experts()
    predictions = [expert.predict(context) for expert in experts]

    print("stage 4: combine meta signal")
    stacker = MetaStacker()
    stacker.set_recent_returns(returns)
    meta_signal = stacker.combine(predictions)
    print(f"  score={meta_signal.score:.3f} conf={meta_signal.confidence:.3f} regime={meta_signal.regime}")

    print("stage 5: select expression")
    selector = MLExpressionSelector(universe=universe)
    expression = selector.select(meta_signal)
    print(f"  type={expression.expression_type} symbols={expression.target_symbols}")

    print("stage 6: optimize portfolio")
    optimizer = PortfolioOptimizer(returns=returns, universe=universe)
    portfolio = optimizer.build_target(expression, regime=meta_signal.regime, signal_score=meta_signal.score)
    print(f"  weights={portfolio.weights}")

    print("stage 7: build derivatives overlay")
    overlay_mgr = DerivativesOverlayManager()
    overlay = overlay_mgr.build_overlay(meta_signal, portfolio)
    print(f"  type={overlay.overlay_type}")

    print("stage 8: pipeline complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Macro Event ML Trading Pipeline")
    parser.add_argument(
        "--mode",
        choices=["mock", "full", "live", "backtest"],
        default="mock",
        help="Pipeline mode: mock (smoke test), full (synthetic), live (Yahoo/FRED), backtest",
    )
    args = parser.parse_args()

    if args.mode == "mock":
        run_mock()
    elif args.mode == "full":
        run_full()
    elif args.mode == "live":
        run_live()
    elif args.mode == "backtest":
        from scripts.run_backtest import main as run_backtest
        run_backtest()


if __name__ == "__main__":
    main()
