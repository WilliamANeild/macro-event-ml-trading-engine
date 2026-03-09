from datetime import date

from src.engine.backtest.engine import BacktestEngine
from src.engine.data.loader import MockDataSource
from src.engine.derivatives.overlay import DerivativesOverlayManager
from src.engine.events.builder import EventFeatureBuilder
from src.engine.expression.selector import ExpressionSelector
from src.engine.experts.registry import get_experts
from src.engine.experts.schemas import ExpertContext
from src.engine.features.builder import FeatureBuilder
from src.engine.meta.stacker import MetaStacker
from src.engine.portfolio.optimizer import PortfolioOptimizer
from src.engine.universe.registry import get_universe


def main() -> None:
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
    feature_row = feature_builder.build(
        as_of_date=as_of_date,
        theme="shipping",
        subtheme="suez",
        prices=prices,
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


if __name__ == "__main__":
    main()