"""Multi-figures and tables PDF export example for PourOver.

Run:
  python examples/pdf/multi_figs_tables.py

Outputs (under examples/out/):
  - multi.md   (Markdown)
  - multi.pdf  (PDF via Report.write_pdf)
"""
from __future__ import annotations

import math
import pathlib
import sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table


def _make_plot_sin_cos(out_dir: pathlib.Path) -> str | None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(3.6, 2.2))
    xs = [i * 0.2 for i in range(0, 32)]
    ax.plot(xs, [math.sin(x) for x in xs], label="sin(x)")
    ax.plot(xs, [math.cos(x) for x in xs], label="cos(x)")
    ax.legend()
    ax.set_title("Sin/Cos")
    fig.tight_layout()
    out = out_dir / "sin_cos.png"
    fig.savefig(out)
    return str(out)


def _make_plot_scatter(out_dir: pathlib.Path) -> str | None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1.0, size=100)
    y = 0.8 * x + rng.normal(0, 0.3, size=100)
    fig, ax = plt.subplots(figsize=(3.2, 2.2))
    ax.scatter(x, y, s=12, alpha=0.8)
    ax.set_title("Scatter")
    fig.tight_layout()
    out = out_dir / "scatter.png"
    fig.savefig(out)
    return str(out)


def build_report() -> Report:
    rpt = Report("Multi Figures + Tables", author="Examples")

    rpt.add_section("Overview").add_text(
        "This example combines multiple plots and tables on a single page (when space allows)",
        "and exports to PDF directly from the Report object.",
    )

    # Figures
    figs = rpt.add_section("Figures")
    out_dir = _ROOT / ".pourover_figs"
    p1 = _make_plot_sin_cos(out_dir)
    p2 = _make_plot_scatter(out_dir)
    if p1:
        figs.add_image_path(p1, alt="sin/cos", caption="Sin and Cos", width="60%")
    if p2:
        figs.add_image_path(p2, alt="scatter", caption="Scatter", width="60%")
    if not (p1 or p2):
        figs.add_text("Matplotlib/numpy not installed — skipping figures.")

    # Tables
    tsec = rpt.add_section("Tables")
    t1 = Table.from_dicts([
        {"Metric": "Accuracy", "Value": "92.8%"},
        {"Metric": "F1", "Value": "91.5%"},
        {"Metric": "ROC AUC", "Value": "0.962"},
    ])
    t2 = Table.from_dicts([
        {"Parameter": "Learning rate", "Value": 3e-4},
        {"Parameter": "Batch size", "Value": 64},
        {"Parameter": "Epochs", "Value": 12},
    ])
    tsec.add_table(t1)
    tsec.add_table(t2)

    return rpt


def main() -> None:
    rpt = build_report()
    out_dir = _ROOT / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "multi.md"
    pdf_path = out_dir / "multi.pdf"

    # Write Markdown
    md_path.write_text(rpt.to_markdown(), encoding="utf-8")

    # PDF via object path
    try:
        rpt.write_pdf(str(pdf_path))
        print(f"Wrote: {pdf_path}")
    except Exception as e:
        print("[Report.write_pdf] ReportLab not available:", e)


if __name__ == "__main__":
    main()
