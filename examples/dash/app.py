"""Dash example for PourOver.

Run:
  python examples/dash/app.py

Open http://127.0.0.1:8050/ in your browser.
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table


def _make_demo_plot():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    xs = [0, 1, 2, 3, 4, 5]
    ys = [0.1, 0.4, 0.35, 0.9, 1.3, 1.6]
    ax.plot(xs, ys, marker="o")
    ax.set_title("Interactive in Dash")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    return fig


def build_report(include_table: bool, include_interactive: bool = False) -> Report:
    rpt = Report("Dash Demo", author="Examples")
    rpt.add_section("Summary").add_text(
        "This report was generated inside Dash.",
        "Use Dash controls to explore tables and plots.",
    )
    if include_table:
        tbl = Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
            ]
        )
        rpt.add_section("Metrics").add_table(tbl)
    if include_interactive:
        fig = _make_demo_plot()
        if fig is not None:
            rpt.add_section("Interactive Plot").add_matplotlib(
                fig,
                out_dir=".pourover_figs",
                filename="dash_interactive.png",
                caption="Zoom/pan in Dash; rendered as PNG in Markdown/PDF.",
                width="65%",
                interactive=True,
            )
    return rpt


if __name__ == "__main__":
    report = build_report(include_table=True, include_interactive=True)
    report.configure_dash(tabs=["Report", "Markdown", "HTML", "PDF"], preview_height="65vh")
    app = report.to_dash_app()
    app.run_server(debug=True)
