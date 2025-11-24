"""Streamlit interactive plots demo for MochaFlow.

Run:
  streamlit run examples/streamlit/sliders_multi.py

This demo builds a richer report with several narrative sections and multiple
matplotlib plots that become interactive (zoom/pan) inside Streamlit/Dash via
Plotly. It uses the built‑in Report.show_streamlit() UI so you can focus on
data and content.
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "mochaflow").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mochaflow.core import Report, Table


def _make_dataset(n: int = 60):
    try:
        import numpy as np  # type: ignore
        import pandas as pd  # type: ignore
    except Exception:
        return None
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, n)
    noise = rng.normal(0, 0.25, size=n)
    y_base = 0.8 * x + noise
    y_offset = 0.8 * x + 1.5 + noise
    y_steep = 1.2 * x + noise
    df = pd.DataFrame({"x": x, "y_base": y_base, "y_offset": y_offset, "y_steep": y_steep})
    return df


def _scatter_plot(df, column: str, title: str):
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.scatter(df["x"], df[column], color="#1f77b4", alpha=0.85, label=column)
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel(column)
    ax.legend()
    fig.tight_layout()
    return fig


def build_report() -> Report:
    rpt = Report("Sliders + Narrative", author="Examples")

    # A wordier introduction to set context
    intro = rpt.add_section("Background")
    intro.add_text(
        "This report illustrates how MochaFlow can render static matplotlib figures ",
        "into Markdown/PDF while automatically upgrading them to interactive Plotly ",
        "charts inside Streamlit/Dash. Use the zoom and pan controls in the Report tab ",
        "to explore each data series; the PDF still receives the same figure as a PNG.",
    )

    df = _make_dataset()
    if df is None:
        intro.add_text(
            "pandas/numpy are not installed, so the interactive charts are omitted. ",
            "Install them with: pip install pandas numpy",
        )
        return rpt

    # Summarize the dataset
    rpt.add_section("Data Summary").add_text(
        "We simulate measurements with three variants: base (m≈0.8), offset (+1.5 intercept), ",
        "and a steeper relationship (m≈1.2). Noise is small and i.i.d., intended to mimic common ",
        "observational scatter. Use the interactive charts below to zoom into regions of interest.",
    )

    # A compact stats table for quick orientation
    try:
        import pandas as pd  # type: ignore
        stats = pd.DataFrame({
            "series": ["y_base", "y_offset", "y_steep"],
            "mean": [float(df[c].mean()) for c in ["y_base", "y_offset", "y_steep"]],
            "std": [float(df[c].std()) for c in ["y_base", "y_offset", "y_steep"]],
        })
        rpt.add_section("Quick Stats").add_table(
            Table(headers=list(stats.columns), rows=stats.values.tolist())
        )
    except Exception:
        pass

    # Three interactive charts with different default/allowed slopes
    s1 = rpt.add_section("Base Relationship")
    s1.add_text(
        "The baseline shows y ≈ 0.8 x with small noise. Zoom/pan in the Report tab or hover ",
        "to inspect values; the PDF receives the same figure as a static PNG.",
    )
    fig1 = _scatter_plot(df, "y_base", "y_base vs x")
    if fig1 is not None:
        s1.add_matplotlib(
            fig1,
            out_dir=".mochaflow_figs",
            filename="y_base.png",
            caption="Baseline relationship (≈0.8 slope).",
            width="70%",
            interactive=True,
        )

    s2 = rpt.add_section("Offset Variant")
    s2.add_text(
        "Here the relationship is shifted upward by a constant offset; the true slope remains ",
        "similar. Use the interactive controls to focus on specific regions.",
    )
    fig2 = _scatter_plot(df, "y_offset", "y_offset vs x")
    if fig2 is not None:
        s2.add_matplotlib(
            fig2,
            out_dir=".mochaflow_figs",
            filename="y_offset.png",
            caption="Offset variant (+1.5 intercept).",
            width="70%",
            interactive=True,
        )

    s3 = rpt.add_section("Steeper Relationship")
    s3.add_text(
        "A steeper series (m≈1.2) accentuates sensitivity in y for the same change in x. ",
        "Interactive zooming helps compare the high-slope region differences.",
    )
    fig3 = _scatter_plot(df, "y_steep", "y_steep vs x")
    if fig3 is not None:
        s3.add_matplotlib(
            fig3,
            out_dir=".mochaflow_figs",
            filename="y_steep.png",
            caption="Steeper relationship (≈1.2 slope).",
            width="70%",
            interactive=True,
        )

    # Closing thoughts for a more narrative feel
    rpt.add_section("Takeaways").add_text(
        "While formal model fitting is essential for inference, quick visual probes with ",
        "interactive charts (zoom, hover, export) can guide intuition and help calibrate ",
        "expectations before deeper analysis.",
    )

    return rpt


if __name__ == "__main__":
    try:
        import streamlit as st  # type: ignore
    except Exception:
        print(build_report().to_markdown())
    else:
        r = build_report()
        # Demonstrate customization: two tabs and taller HTML preview
        r.configure_streamlit(tabs=["Report", "Markdown", "HTML"], height=560)
        r.show_streamlit()
