"""Simple end-to-end EasyPour example.

Usage:
  python examples/playbook/simple_full.py           # write Markdown + PDF
  python examples/playbook/simple_full.py --preview dash
  streamlit run examples/playbook/simple_full.py -- --preview streamlit
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from easypour import Report, Table

ROOT = pathlib.Path(__file__).resolve().parents[2]
if (ROOT / "easypour").exists() and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_plot():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.0, 2.0))
    xs = [0, 1, 2, 3, 4]
    ys = [0.2, 0.6, 0.9, 1.1, 1.4]
    ax.plot(xs, ys, marker="o", color="#1f77b4")
    ax.set_title("Latency Trend")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Latency (ms)")
    fig.tight_layout()
    return fig


def build_report() -> Report:
    """Construct a sample report that mixes layouts and artifacts."""
    rpt = Report("Quarterly Snapshot", author="EasyPour Examples").configure_pdf(
        page_layouts=["single", ("two", 3), "single"]
    )
    summary = rpt.add_section("Summary")
    summary.add_text(
        "This lightweight report demonstrates the EasyPour workflow.",
        "We capture a short narrative, a metrics table, and a simple figure.",
    )

    rpt.add_section("Metrics").add_table(
        Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "Latency", "Value": "1.4 ms"},
                {"Metric": "Throughput", "Value": "2.1k req/s"},
            ]
        ),
        caption="Key model metrics from the latest evaluation.",
        label="tab:metrics",
        numbered=True,
    )

    plot = _make_plot()
    if plot is not None:
        rpt.add_section("Figure").add_matplotlib(
            plot,
            out_dir=".easypour_figs",
            filename="quarterly_latency.png",
            caption="Latency decreases as tuning iterations progress.",
            width="70%",
            interactive=True,
            label="fig:latency",
            numbered=True,
        )

    rpt.add_section("Notes").add_text(
        f"See {rpt.ref('tab:metrics')} for the full metric snapshot and {rpt.ref('fig:latency')} "
        "for the raw latency trend."
    )

    appendix = rpt.add_section("Appendix")
    appendix.add_layout_block(
        "single",
        Table.from_dicts(
            [
                {"Item": "Owner", "Value": "ML Team"},
                {"Item": "Revision", "Value": "2025Q1"},
                {"Item": "Pipeline", "Value": "exp://snapshot"},
            ]
        ),
        keep_together=True,
        page_break_after=False,
    )
    rpt.add_page_break()
    return rpt


def _write_outputs(report: Report, name: str) -> None:
    out_dir = ROOT / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"{name}.md"
    report.write_markdown(md_path)
    print(f"[ok] Markdown: {md_path}")

    pdf_path = out_dir / f"{name}.pdf"
    try:
        report.write_pdf(pdf_path)
        print(f"[ok] PDF     : {pdf_path}")
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"[warn] PDF skipped ({exc})")


def _preview_streamlit(report: Report) -> None:
    try:
        import streamlit as st  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Streamlit preview requested but Streamlit is not installed.") from exc

    st.set_page_config(page_title=f"EasyPour — {report.title}", layout="wide")
    report.show_streamlit(height=520)


def _preview_dash(report: Report) -> None:
    try:
        report.configure_dash(tabs=["Report", "Markdown", "HTML", "PDF"], preview_height="65vh")
        app = report.to_dash_app()
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Dash preview requested but Dash is not installed.") from exc

    app.run_server(debug=True)


def main():
    """Entry point for CLI/preview invocations."""
    parser = argparse.ArgumentParser(description="Simple EasyPour workflow example.")
    parser.add_argument(
        "--preview", choices=["streamlit", "dash"], help="Preview the report instead of exiting."
    )
    args = parser.parse_args()

    rpt = build_report()
    _write_outputs(rpt, "simple_full")

    if args.preview == "streamlit":
        _preview_streamlit(rpt)
    elif args.preview == "dash":
        _preview_dash(rpt)


if __name__ == "__main__":
    main()
