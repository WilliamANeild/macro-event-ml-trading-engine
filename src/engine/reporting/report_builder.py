from __future__ import annotations

from src.engine.backtest.metrics import compute_calmar, compute_sortino
from src.engine.backtest.schemas import BacktestResult


class ReportBuilder:
    def build_summary(self, result: BacktestResult) -> str:
        sortino = compute_sortino(result.returns)
        calmar = compute_calmar(result.returns, result.equity_curve)
        lines = [
            "=" * 50,
            "BACKTEST SUMMARY REPORT",
            "=" * 50,
            f"Sharpe Ratio:     {result.sharpe:.3f}",
            f"Sortino Ratio:    {sortino:.3f}",
            f"Calmar Ratio:     {calmar:.3f}",
            f"Max Drawdown:     {result.max_drawdown:.3%}",
            f"Final Equity:     {result.metadata.get('final_equity', 'N/A')}",
            f"Hit Rate:         {result.metadata.get('hit_rate', 0):.1%}",
            f"Total Days:       {result.metadata.get('n_days', 0)}",
            f"Rebalances:       {result.metadata.get('n_rebalances', 0)}",
            f"Total Costs:      {result.metadata.get('total_costs', 0):.6f}",
            f"Total Return:     {sum(result.returns):.4%}" if result.returns else "Total Return: N/A",
            "",
            "--- Benchmark Comparison ---",
            f"SPY Sharpe:       {result.benchmark_sharpe.get('SPY', 0):.3f}",
            f"60/40 Sharpe:     {result.benchmark_sharpe.get('60_40', 0):.3f}",
            f"Info Ratio (SPY): {result.metadata.get('info_ratio_vs_spy', 0):.3f}",
            f"Excess vs SPY:    {(sum(result.returns) - sum(result.benchmark_returns.get('SPY', []))):.4%}"
            if result.returns and result.benchmark_returns.get("SPY")
            else "Excess vs SPY:    N/A",
            f"Excess vs 60/40:  {(sum(result.returns) - sum(result.benchmark_returns.get('60_40', []))):.4%}"
            if result.returns and result.benchmark_returns.get("60_40")
            else "Excess vs 60/40:  N/A",
            "=" * 50,
        ]
        return "\n".join(lines)

    def build_event_report(self, result: BacktestResult) -> str:
        lines = ["EVENT IMPACT REPORT", "-" * 40]
        for evt in result.event_log:
            lines.append(
                f"  {evt.get('date', '?')} | theme={evt.get('theme', '?')} "
                f"| intensity={evt.get('intensity', 0):.3f}"
            )
        if not result.event_log:
            lines.append("  No significant events detected.")
        return "\n".join(lines)

    def build_attribution_report(self, result: BacktestResult) -> str:
        attr = result.attribution
        lines = ["RETURN ATTRIBUTION", "-" * 40]
        by_theme = attr.get("by_theme", {})
        for theme, pnl in by_theme.items():
            lines.append(f"  {theme}: {pnl:.6f}")
        lines.append(f"  Hedge contribution:  {attr.get('hedge_contribution', 0):.6f}")
        lines.append(f"  Overlay contribution: {attr.get('overlay_contribution', 0):.6f}")
        lines.append(f"  Cost drag:           {attr.get('total_cost_drag', 0):.6f}")
        return "\n".join(lines)
