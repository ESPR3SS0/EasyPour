"""Streamlit example for PourOver.

Run:
  streamlit run examples/streamlit/app.py

This demo builds a small report and then delegates UI rendering to
`Report.show_streamlit()` which displays Markdown, an HTML preview, and a PDF
download button with sensible defaults.
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table, Image


def _make_demo_plot():
    """Create a tiny matplotlib figure for the demo (no heavy deps)."""
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.plot([0, 1, 2, 3], [0.0, 0.8, 0.3, 1.2], marker="o")
    ax.set_title("Demo Plot")
    ax.set_xlabel("Step")
    ax.set_ylabel("Value")
    fig.tight_layout()
    return fig


def build_report(
    include_table: bool,
    include_image: bool,
    include_plot: bool = False,
    include_dataframe: bool = False,
) -> Report:
    rpt = Report("Streamlit Demo", author="Examples")
    rpt.add_section("Summary").add_text(
        "This report was generated inside Streamlit.",
        "Toggle options in the sidebar to include extra content.",
    )
    if include_table:
        tbl = Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
            ]
        )
        rpt.add_section("Metrics").add_table(tbl)
    if include_image:
        # Use a placeholder; users can replace with a real path
        try:
            import streamlit as st  # imported here to avoid hard dependency on import
            placeholder_path = str(st.__file__)
        except Exception:
            placeholder_path = "./path/to/your/image.png"
        rpt.add_section("Artifacts").add_image_path(
            path=placeholder_path, alt="placeholder", caption="Replace with your image"
        )
    if include_plot:
        fig = _make_demo_plot()
        if fig is not None:
            rpt.add_section("Plot").add_matplotlib(
                fig,
                out_dir=".pourover_figs",
                filename="demo_plot.png",
                caption="A tiny demo plot",
                width="60%",
            )
        else:
            # Matplotlib not available; add a friendly note
            rpt.add_section("Plot").add_text("Matplotlib not installed; no plot shown.")
    if include_dataframe:
        try:
            import pandas as pd  # type: ignore
            df = pd.DataFrame(
                {
                    "feature": ["f1", "f2", "f3"],
                    "mean": [0.12, -0.03, 1.05],
                    "std": [0.08, 0.14, 0.22],
                }
            )
            # Convert DataFrame to a PourOver Table for consistent rendering
            tbl = Table(headers=list(df.columns), rows=df.values.tolist())
            rpt.add_section("Pandas DataFrame").add_table(tbl)
        except Exception:
            rpt.add_section("Pandas DataFrame").add_text("pandas not installed; no DataFrame shown.")
    return rpt


if __name__ == "__main__":
    # Interactive toggles and preview using built-in helper
    try:
        import streamlit as st  # type: ignore
    except Exception:
        # If run outside `streamlit run`, silently build and exit
        rpt = build_report(include_table=True, include_image=False, include_plot=True)
        print(rpt.to_markdown())
    else:
        st.set_page_config(page_title="PourOver + Streamlit", layout="wide")
        st.title("PourOver + Streamlit")
        st.sidebar.header("Options")
        opt_table = st.sidebar.checkbox("Include table", value=True)
        opt_image = st.sidebar.checkbox("Include image placeholder", value=False)
        opt_plot = st.sidebar.checkbox("Include matplotlib plot", value=True)
        opt_df = st.sidebar.checkbox("Include pandas DataFrame", value=True)
        opt_interactive = st.sidebar.checkbox("Include interactive (plotly) view", value=True)
        rpt = build_report(opt_table, opt_image, opt_plot, opt_df)
        if opt_interactive:
            fig = _make_demo_plot()
            if fig is not None:
                rpt.add_section("Interactive Plot").add_matplotlib(
                    fig,
                    out_dir=".pourover_figs",
                    filename="interactive_demo.png",
                    caption="Zoom/pan in Streamlit/Dash via Plotly; rendered as PNG in Markdown/PDF.",
                    width="70%",
                    interactive=True,
                )
        rpt.show_streamlit(height=520)
