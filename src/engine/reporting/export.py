from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.engine.backtest.schemas import BacktestResult
from .report_builder import ReportBuilder
from .visualizations import (
    plot_drawdown,
    plot_equity_curve,
    plot_event_impact,
    plot_exposure_over_time,
)


def export_to_csv(result: BacktestResult, output_dir: str = "output") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pd.DataFrame({"equity": result.equity_curve}).to_csv(out / "equity_curve.csv", index=False)
    pd.DataFrame({"returns": result.returns}).to_csv(out / "returns.csv", index=False)
    if result.trades:
        pd.DataFrame(result.trades).to_csv(out / "trades.csv", index=False)
    pd.DataFrame({"drawdown": result.drawdowns}).to_csv(out / "drawdowns.csv", index=False)


def export_summary_html(result: BacktestResult, output_dir: str = "output") -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    builder = ReportBuilder()
    summary = builder.build_summary(result)
    attribution = builder.build_attribution_report(result)
    events = builder.build_event_report(result)

    # Generate charts as base64
    charts_html = ""
    for name, plot_fn in [
        ("Equity Curve", plot_equity_curve),
        ("Drawdown", plot_drawdown),
        ("Exposure", plot_exposure_over_time),
        ("Events", plot_event_impact),
    ]:
        fig = plot_fn(result)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        charts_html += f'<h2>{name}</h2><img src="data:image/png;base64,{b64}" width="800"/>\n'

    html = f"""<!DOCTYPE html>
<html><head><title>Backtest Report</title>
<style>body{{font-family:monospace;margin:2em;}} pre{{background:#f4f4f4;padding:1em;}} img{{margin:1em 0;}}</style>
</head><body>
<h1>Backtest Report</h1>
<pre>{summary}</pre>
<pre>{attribution}</pre>
<pre>{events}</pre>
{charts_html}
</body></html>"""

    path = out / "report.html"
    path.write_text(html)
    return str(path)
