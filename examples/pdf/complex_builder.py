"""Complex PDF export example for PourOver.

Run (generate Markdown + PDF to examples/out/):
  python examples/pdf/complex_builder.py

This builds a richer report with multiple sections, nested content,
tables, and a matplotlib figure (if available), then exports to PDF.
"""
from __future__ import annotations

import os
import pathlib
import sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table


def _maybe_matplotlib_plot(out_dir: pathlib.Path) -> str | None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.plot([0, 1, 2, 3], [0.0, 0.9, 0.2, 1.1], marker="o")
    ax.set_title("Throughput")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "throughput.png"
    fig.tight_layout()
    fig.savefig(out)
    return str(out)


def build_report() -> Report:
    rpt = Report("Complex Export", author="Examples", meta={"draft": False, "rev": 2})

    rpt.add_section("Executive Summary").add_text(
        "This document summarizes key model performance metrics, artifacts, and notes.",
        "It demonstrates PourOver's ability to export a nicely formatted PDF from",
        "simple Python objects and Markdown composition.",
    )

    # Metrics table
    metrics = Table.from_dicts(
        [
            {"Metric": "Accuracy", "Value": "92.8%"},
            {"Metric": "F1", "Value": "91.5%"},
            {"Metric": "Latency (P95)", "Value": "84ms"},
        ]
    )
    rpt.add_section("Metrics").add_table(metrics)

    # Artifacts: include a generated plot if matplotlib is available
    artifacts = rpt.add_section("Artifacts")
    img_path = _maybe_matplotlib_plot(_ROOT / ".pourover_figs")
    if img_path:
        artifacts.add_image_path(img_path, alt="throughput", caption="Model throughput over time", width="60%")
    else:
        artifacts.add_text("Matplotlib not installed; skipping figure.")

    # Nested notes
    notes = rpt.add_section("Notes")
    blockers = notes.add_section("Deploy Blockers")
    blockers.add_bullets(["Memory regression when enabling BN folding", "GPU peak spikes in spike tests"])
    todos = notes.add_section("Follow‑ups")
    todos.add_checklist([("Quantization pass on branch exp/quant", False), ("Re‑benchmark ONNX export", True)])

    return rpt


def main() -> None:
    rpt = build_report()
    out_dir = _ROOT / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "complex.md"
    pdf_path = out_dir / "complex.pdf"
    # Write Markdown for reference
    md_path.write_text(rpt.to_markdown(), encoding="utf-8")
    # Export PDF via ReportLab template
    try:
        rpt.write_pdf(str(pdf_path))
        print(f"Wrote: {pdf_path}")
    except Exception as e:
        print("PDF export unavailable (install reportlab).", e)


if __name__ == "__main__":
    main()
