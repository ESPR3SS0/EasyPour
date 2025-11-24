"""IEEE-style report builder example.

Run:
  python examples/pdf/ieee_builder.py

Outputs (under examples/out/):
  - ieee_sample.md
  - ieee_sample.pdf  (using IEEETemplate)
"""

from __future__ import annotations

import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mochaflow import Report, Table
from mochaflow.ieee import IEEETemplate


def _ensure_asset() -> pathlib.Path:
    assets = ROOT / "examples" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    png = assets / "latency_tiny.png"
    if not png.exists():
        data = (
            "iVBORw0KGgoAAAANSUhEUgAAAFAAAAAUCAYAAABXi6xwAAAABHNCSVQICAgIfAhkiAAAAC1J"
            "REFUeJztwTEBAAAAwqD1T20KP6AAAAAAAAAAAAAAAAAAAAAAAH4Bp3wAATW7VwkAAAAASUVO"
            "RK5CYII="
        )
        png.write_bytes(base64.b64decode(data))
    return png


def build_report(asset_path: pathlib.Path) -> Report:
    rpt = Report("Sample IEEE Paper", author="A. Researcher, B. Scientist")
    rpt.add_reference("smith19", "J. Smith and R. Jones, \"Neural Widgets,\" IEEE Trans., 2019.")
    rpt.add_reference("nguyen21", "P. Nguyen, \"Accelerating Edge Models,\" Proc. IEEE, 2021.")

    abstract = rpt.add_section("Abstract")
    abstract.add_text(
        "This sample demonstrates MochaFlow's two-column PDF capabilities. "
        "It includes figures, tables, references, and citations."
    )

    intro = rpt.add_section("I. Introduction")
    intro.add_text(
        f"Edge accelerators continue to evolve {rpt.cite('smith19')}, requiring "
        "robust reporting tools that keep up with publication-quality layouts."
    )

    method = rpt.add_section("II. Methodology")
    method.add_text(
        "We generate Markdown first, then convert it to a structured PDF using "
        "MochaFlow's `Report.write_pdf()` and `IEEETemplate`."
    )
    method.add_figure(asset_path, caption="Latency trend for the proposed system.", label="fig:latency", width="70%")

    results = rpt.add_section("III. Results")
    results.add_table(
        Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "93.1%"},
                {"Metric": "F1", "Value": "91.8%"},
                {"Metric": "Throughput (req/s)", "Value": "1.2k"},
            ]
        ),
        caption="Evaluation metrics on the EdgeBench dataset.",
        label="tab:metrics",
        numbered=True,
    )
    results.add_text(f"Metrics outperform the baseline reported in {rpt.cite('nguyen21')} by 7%.")

    rpt.ensure_references_section()
    return rpt


def main() -> None:
    asset = _ensure_asset()
    rpt = build_report(asset)
    out_dir = ROOT / "examples" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "ieee_sample.md"
    pdf_path = out_dir / "ieee_sample.pdf"
    md_path.write_text(rpt.to_markdown(), encoding="utf-8")

    template = IEEETemplate(
        running_header_left="IEEE PREPRINT",
        running_header_right="Sample Paper",
        include_page_numbers=True,
    )
    rpt.write_pdf(str(pdf_path), template=template)
    print(f"Wrote Markdown: {md_path}")
    print(f"Wrote PDF     : {pdf_path}")


if __name__ == "__main__":
    main()
