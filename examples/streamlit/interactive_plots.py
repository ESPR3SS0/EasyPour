"""Streamlit interactive Matplotlib => Plotly demo for EasyPour.

Run:
  streamlit run examples/streamlit/interactive_plots.py
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if (ROOT / "easypour").exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easypour.core import Report


def _make_plot(scale: float, title: str):
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    xs = [0, 1, 2, 3, 4, 5]
    ys = [scale * x + (x % 2 - 0.5) * 0.4 for x in xs]
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.plot(xs, ys, marker="o", color="#1f77b4")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.tight_layout()
    return fig


def build_report() -> Report:
    rpt = Report("Interactive Figures", author="Examples")
    intro = rpt.add_section("Overview")
    intro.add_text(
        "Matplotlib figures render as static PNGs in Markdown/PDF, but setting `interactive=True` ",
        "automatically upgrades them to Plotly in Streamlit/Dash so you can zoom, pan, and hover.",
    )

    for scale, title in [(0.5, "Gentle trend"), (1.2, "Steeper trend")]:
        fig = _make_plot(scale, title)
        sec = rpt.add_section(title)
        if fig is None:
            sec.add_text("Matplotlib is not installed in this environment.")
            continue
        sec.add_matplotlib(
            fig,
            out_dir=".easypour_figs",
            filename=f"interactive_{scale:.1f}.png",
            caption=f"{title} — zoom/pan in Streamlit; static in PDF.",
            width="70%",
            interactive=True,
            numbered=True,
        )
    return rpt


if __name__ == "__main__":
    try:
        import streamlit as st  # type: ignore
    except Exception:
        print(build_report().to_markdown())
    else:
        st.set_page_config(page_title="EasyPour Interactive Figures", layout="wide")
        build_report().show_streamlit(height=540)
