"""Streamlit customization + PDF export example for PourOver.

Run:
  streamlit run examples/streamlit/pdf_with_customization.py

This example customizes the Streamlit preview via hooks and options, and also
exports a PDF to examples/out/streamlit_custom.pdf (when ReportLab is installed).
"""
from __future__ import annotations

import io
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table


def build_report() -> Report:
    rpt = Report("Streamlit Custom + PDF", author="Examples")
    rpt.add_section("Summary").add_text(
        "This preview demonstrates custom Streamlit hooks (sidebar, lifecycle) while ",
        "still exporting the same content to a nice PDF file.",
    )
    rpt.add_section("Metrics").add_table(
        Table.from_dicts([
            {"Metric": "AUC", "Value": "0.962"},
            {"Metric": "Recall", "Value": "0.904"},
        ])
    )
    return rpt


def make_sidebar(st, report):  # noqa: N802
    st.header("Controls")
    st.checkbox("Include appendix", key="include_appendix", value=True)


def before_render(st, report):  # noqa: N802
    st.info("This is a custom banner rendered before tabs are created.")


def after_render(st, report):  # noqa: N802
    st.success("Rendered after tabs — you can place extra notes here.")


def _export_pdf(rpt: Report, out_pdf: pathlib.Path) -> str | None:
    try:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        rpt.write_pdf(str(out_pdf))
        return str(out_pdf)
    except Exception as e:  # pragma: no cover
        return None


if __name__ == "__main__":
    try:
        import streamlit as st  # type: ignore
    except Exception:
        # Non-streamlit run — just export a PDF
        rpt = build_report()
        out = _ROOT / "examples" / "out" / "streamlit_custom.pdf"
        path = _export_pdf(rpt, out)
        print("PDF:", path or "[missing reportlab]")
    else:
        rpt = build_report()
        # Optionally add an appendix based on sidebar toggle
        def _sidebar(stmod, rep):
            make_sidebar(stmod, rep)
            if stmod.session_state.get("include_appendix", True):
                rep.add_section("Appendix").add_text("Extra notes available when enabled in the sidebar.")

        rpt.configure_streamlit(page_title="PourOver — Custom PDF", layout="wide", height=560)
        rpt.set_streamlit_hooks(sidebar=_sidebar, before_render=before_render, after_render=after_render)

        # Provide an explicit "Save to disk" in addition to the built-in PDF tab
        with st.sidebar:
            if st.button("Export PDF to examples/out"):
                path = _export_pdf(rpt, _ROOT / "examples" / "out" / "streamlit_custom.pdf")
                if path:
                    st.success(f"Saved: {path}")
                else:
                    st.error("ReportLab not installed — cannot export PDF.")

        rpt.show_streamlit()
