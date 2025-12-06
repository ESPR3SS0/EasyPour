"""Advanced end-to-end EasyPour example with references and interactive figures.

Usage:
  python examples/playbook/advanced_full.py           # write Markdown + PDF (IEEE template)
  python examples/playbook/advanced_full.py --preview dash
  streamlit run examples/playbook/advanced_full.py -- --preview streamlit
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Optional

from easypour import Report, Table
from easypour.ieee import IEEETemplate

ROOT = pathlib.Path(__file__).resolve().parents[2]
if (ROOT / "easypour").exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_wave_plot(freq: float, title: str):
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    xs = np.linspace(0, 4 * np.pi, 240)
    ys = np.sin(freq * xs)
    fig, ax = plt.subplots(figsize=(3.6, 2.2))
    ax.plot(xs, ys, color="#d62728")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("sin(fx)")
    fig.tight_layout()
    return fig


def build_report() -> Report:
    rpt = Report("Edge Forecast Deep Dive", author="EasyPour Labs", meta={"figure_prefix": "Fig.", "table_prefix": "Table"})
    rpt.add_reference("smith19", "J. Smith et al., 'Neural Widgets', IEEE, 2019.")
    rpt.add_reference("lee22", "A. Lee, 'Optimizing Edge Pipelines', Proc. IEEE, 2022.")

    intro = rpt.add_section("I. Introduction")
    intro.add_text(
        "We explore the latest edge-model forecast and highlight where latency gains originate,",
        f"drawing on {rpt.cite('smith19')} for baseline comparisons.",
    )

    table_sec = rpt.add_section("II. Metrics Snapshot")
    table_sec.add_table(
        Table.from_dicts(
            [
                {"Metric": "Latency (P95)", "Value": "1.2 ms"},
                {"Metric": "Throughput", "Value": "2.4k req/s"},
                {"Metric": "Energy", "Value": "18 mJ"},
            ]
        ),
        caption="Key performance indicators for the optimized edge stack.",
        label="tab:metrics",
        numbered=True,
    )

    fig_sec = rpt.add_section("III. Frequency Response")
    fig_sec.add_text(
        "Interactive figures let reviewers zoom/pan within Streamlit or Dash while maintaining the same PNG in PDF.",
        "Figure references stay consistent everywhere.",
    )
    for freq in (0.5, 1.0, 1.5):
        fig = _make_wave_plot(freq, f"Response at f={freq}")
        if fig is None:
            fig_sec.add_text("Matplotlib/numpy not installed; no figure rendered.")
            break
        fig_sec.add_matplotlib(
            fig,
            out_dir=".easypour_figs",
            filename=f"advanced_freq_{freq}.png",
            caption=f"Response curve for frequency {freq}.",
            width="78%",
            interactive=True,
            label=f"fig:freq{freq}",
            numbered=True,
        )

    rpt.add_section("IV. Discussion").add_text(
        f"Table {rpt.ref('tab:metrics')} summarizes the KPIs, while {rpt.ref('fig:freq1.0')} highlights the nominal response.",
        "Refer to {0} for additional context.".format(rpt.cite('lee22')),
    )

    rpt.ensure_references_section()
    return rpt


def _write_outputs(report: Report, name: str) -> None:
    out_dir = ROOT / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"{name}.md"
    report.write_markdown(md_path)
    print(f"[ok] Markdown: {md_path}")

    pdf_path = out_dir / f"{name}.pdf"
    try:
        report.write_pdf(pdf_path, template=IEEETemplate())
        print(f"[ok] PDF     : {pdf_path}")
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"[warn] PDF skipped ({exc})")


def _preview_streamlit(report: Report) -> None:
    try:
        import streamlit as st  # type: ignore
    except Exception as exc:
        raise RuntimeError("Streamlit preview requested but Streamlit is not installed.") from exc

    st.set_page_config(page_title=f"EasyPour — {report.title}", layout="wide")
    report.show_streamlit(height=560)


def _preview_dash(report: Report) -> None:
    try:
        report.configure_dash(tabs=["Report", "Markdown", "HTML", "PDF"], preview_height="70vh")
        app = report.to_dash_app()
    except Exception as exc:
        raise RuntimeError("Dash preview requested but Dash is not installed.") from exc

    app.run_server(debug=True)


def main():
    parser = argparse.ArgumentParser(description="Advanced EasyPour workflow example.")
    parser.add_argument("--preview", choices=["streamlit", "dash"], help="Preview the report instead of exiting.")
    args = parser.parse_args()

    rpt = build_report()
    _write_outputs(rpt, "advanced_full")

    if args.preview == "streamlit":
        _preview_streamlit(rpt)
    elif args.preview == "dash":
        _preview_dash(rpt)


if __name__ == "__main__":
    main()
