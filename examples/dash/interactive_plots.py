"""Dash interactive Matplotlib => Plotly demo for EasyPour.

Run:
  python examples/dash/interactive_plots.py
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if (ROOT / "easypour").exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easypour.core import Report


def _make_plot(frequency: float, title: str):
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    xs = np.linspace(0, 4 * np.pi, 180)
    ys = np.sin(frequency * xs)
    fig, ax = plt.subplots(figsize=(3.6, 2.2))
    ax.plot(xs, ys, color="#d62728")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("sin(fx)")
    fig.tight_layout()
    return fig


def build_report() -> Report:
    rpt = Report("Dash Interactive Figures", author="Examples")
    rpt.add_section("Summary").add_text(
        "This example converts Matplotlib figures to Plotly when viewed in Dash via `interactive=True`.",
        "The PDF still receives a static PNG for each figure.",
    )
    for freq in (0.5, 1.0, 2.0):
        fig = _make_plot(freq, f"Frequency {freq}")
        sec = rpt.add_section(f"Frequency {freq}")
        if fig is None:
            sec.add_text("Matplotlib/numpy not installed; no figure rendered.")
            continue
        sec.add_matplotlib(
            fig,
            out_dir=".easypour_figs",
            filename=f"dash_freq_{freq}.png",
            caption="Zoom/pan within Dash; static PNG in Markdown/PDF.",
            width="75%",
            interactive=True,
        )
    return rpt


if __name__ == "__main__":
    rpt = build_report()
    rpt.configure_dash(tabs=["Report", "Markdown", "HTML", "PDF"], preview_height="65vh")
    app = rpt.to_dash_app()
    app.run_server(debug=True)
