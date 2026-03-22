from src.engine.backtest.schemas import BacktestResult
from src.engine.reporting.report_builder import ReportBuilder


def _make_result():
    return BacktestResult(
        returns=[0.01, -0.005, 0.008],
        trades=[{"date": "2024-01-01", "weights": {"XLE": 0.5}}],
        costs=[0.001],
        equity_curve=[1.0, 1.01, 1.005, 1.013],
        drawdowns=[0.0, 0.0, -0.005, 0.0],
        sharpe=1.2,
        max_drawdown=-0.005,
        attribution={"by_theme": {"energy": 0.01}, "hedge_contribution": 0.001,
                      "overlay_contribution": -0.0005, "total_cost_drag": 0.001},
        event_log=[{"date": "2024-01-01", "theme": "energy", "intensity": 0.5}],
        metadata={"final_equity": 1.013, "hit_rate": 0.67, "n_days": 3,
                  "n_rebalances": 1, "total_costs": 0.001},
    )


def test_summary_report():
    builder = ReportBuilder()
    report = builder.build_summary(_make_result())
    assert "Sharpe Ratio" in report
    assert "Max Drawdown" in report


def test_event_report():
    builder = ReportBuilder()
    report = builder.build_event_report(_make_result())
    assert "EVENT IMPACT" in report
    assert "energy" in report


def test_attribution_report():
    builder = ReportBuilder()
    report = builder.build_attribution_report(_make_result())
    assert "RETURN ATTRIBUTION" in report
    assert "energy" in report
