"""Streamlit + Matplotlib example for MochaFlow.

Run:
  streamlit run examples/streamlit/matplotlib_app.py
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "mochaflow").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import matplotlib.pyplot as plt

from mochaflow.core import Report, Table


def _make_line_chart():
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.plot([0, 1, 2, 3], [0, 1, 0.5, 1.5], marker="o")
    ax.set_title("Latency")
    ax.set_xlabel("Step")
    ax.set_ylabel("ms")
    fig.tight_layout()
    return fig


def _make_hist():
    import numpy as np
    rng = np.random.default_rng(0)
    data = rng.normal(loc=0.0, scale=1.0, size=250)
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.hist(data, bins=20, color="#4e79a7")
    ax.set_title("Score Distribution")
    fig.tight_layout()
    return fig


st.set_page_config(page_title="MochaFlow + Streamlit + Matplotlib", layout="wide")
st.title("MochaFlow + Streamlit + Matplotlib")

st.sidebar.header("Options")
opt_table = st.sidebar.checkbox("Include metrics table", value=True)
opt_line = st.sidebar.checkbox("Include line chart", value=True)
opt_hist = st.sidebar.checkbox("Include histogram", value=True)

rpt = Report("Charts Demo", author="Examples")
rpt.add_section("Summary").add_text(
    "This report includes matplotlib figures embedded as images via add_matplotlib().",
)

if opt_table:
    rpt.add_section("Metrics").add_table(
        Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
            ]
        )
    )

sec = rpt.add_section("Figures")
if opt_line:
    sec.add_matplotlib(_make_line_chart(), out_dir=".mochaflow_figs", filename="latency.png", caption="Latency over steps", width="60%")
if opt_hist:
    sec.add_matplotlib(_make_hist(), out_dir=".mochaflow_figs", filename="hist.png", caption="Distribution", width="60%")

# Use the built-in preview — the Markdown tab renders with native Streamlit widgets
rpt.show_streamlit(height=520)
