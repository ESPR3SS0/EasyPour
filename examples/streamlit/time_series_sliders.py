"""Streamlit time‑series interactive plots demo for PourOver.

Run:
  streamlit run examples/streamlit/time_series_sliders.py

Shows two interactive plots (zoom/pan via Plotly in Streamlit/Dash) against synthetic time series.
"""
from __future__ import annotations

import pathlib, sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report


def _make_ts(n: int = 80):
    try:
        import numpy as np  # type: ignore
        import pandas as pd  # type: ignore
    except Exception:
        return None
    rng = np.random.default_rng(7)
    t = np.arange(n)
    y_a = 0.05 * t + rng.normal(0, 0.6, size=n)
    y_b = 0.12 * t + rng.normal(0, 0.6, size=n)
    return pd.DataFrame({"t": t, "y_a": y_a, "y_b": y_b})


def _plot_series(df, column: str, title: str):
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.6, 2.4))
    ax.plot(df["t"], df[column], color="#1f77b4")
    ax.set_title(title)
    ax.set_xlabel("t")
    ax.set_ylabel(column)
    fig.tight_layout()
    return fig


def build_report() -> Report:
    rpt = Report("Time Series + Interactivity", author="Examples")
    intro = rpt.add_section("Overview").add_text(
        "We simulate two time series with different underlying trends. Each figure below is ",
        "generated with matplotlib for Markdown/PDF, but automatically upgraded to Plotly for ",
        "Streamlit/Dash so you can zoom/pan and inspect points interactively.",
    )
    df = _make_ts()
    if df is None:
        rpt.add_section("Note").add_text("Install pandas and numpy to view interactive charts.")
        return rpt

    sec_a = rpt.add_section("Series A")
    sec_a.add_text("Trend ≈ 0.05 per step with modest noise. Zoom to inspect local deviations.")
    fig_a = _plot_series(df, "y_a", "Series A")
    if fig_a is not None:
        sec_a.add_matplotlib(
            fig_a,
            out_dir=".pourover_figs",
            filename="series_a.png",
            caption="Series A (slow trend).",
            width="70%",
            interactive=True,
        )

    sec_b = rpt.add_section("Series B")
    sec_b.add_text("Steeper trend (~0.12 per step). Hover to read precise values.")
    fig_b = _plot_series(df, "y_b", "Series B")
    if fig_b is not None:
        sec_b.add_matplotlib(
            fig_b,
            out_dir=".pourover_figs",
            filename="series_b.png",
            caption="Series B (steeper trend).",
            width="70%",
            interactive=True,
        )

    rpt.add_section("Discussion").add_text(
        "Interactive zooming provides a quick gut-check for linear trend strength and ",
        "direction, even when formal fitting comes later in the analysis pipeline.",
    )
    return rpt


if __name__ == "__main__":
    try:
        import streamlit as st  # type: ignore
    except Exception:
        print(build_report().to_markdown())
    else:
        r = build_report()
        r.show_streamlit(height=540)
