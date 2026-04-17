from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.engine.backtest.walk_forward import WalkForwardBacktester
from src.engine.data.synthetic import SyntheticDataGenerator
from src.engine.reporting.export import export_summary_html, export_to_csv
from src.engine.reporting.report_builder import ReportBuilder
from src.engine.reporting.visualizations import (
    plot_drawdown,
    plot_equity_curve,
    plot_event_impact,
    plot_exposure_over_time,
)


def main(data_mode: str = "synthetic") -> None:
    print("=" * 50)
    print("WALK-FORWARD BACKTEST")
    print("=" * 50)

    output_dir = "output"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    returns = None
    if data_mode == "live":
        print("Loading live market data...")
        from src.engine.data.yahoo_loader import YahooDataSource
        from src.engine.universe.registry import get_universe

        universe = get_universe()
        symbols = [inst.symbol for inst in universe]
        yahoo = YahooDataSource()
        returns = yahoo.load_returns(symbols, start_date="2022-01-01")
        print(f"Loaded {len(returns)} days of live data")

    print("Running walk-forward backtest...")
    data_gen = SyntheticDataGenerator()
    backtester = WalkForwardBacktester(data_gen=data_gen, rebalance_freq=5)
    result = backtester.run(returns=returns)

    # Print summary
    builder = ReportBuilder()
    print(builder.build_summary(result))
    print(builder.build_attribution_report(result))
    print(builder.build_event_report(result))

    # Export CSV
    export_to_csv(result, output_dir)
    print(f"CSV data exported to {output_dir}/")

    # Save charts
    import matplotlib.pyplot as plt

    for name, plot_fn in [
        ("equity_curve", plot_equity_curve),
        ("drawdown", plot_drawdown),
        ("exposure", plot_exposure_over_time),
        ("events", plot_event_impact),
    ]:
        fig = plot_fn(result)
        fig.savefig(f"{output_dir}/{name}.png", dpi=150)
        plt.close(fig)
    print(f"Charts saved to {output_dir}/")

    # HTML report
    html_path = export_summary_html(result, output_dir)
    print(f"HTML report: {html_path}")

    print("\nBacktest complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument("--data", choices=["synthetic", "live"], default="synthetic")
    args = parser.parse_args()
    main(data_mode=args.data)
