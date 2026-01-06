"""IEEE-style report builder example.

Run:
  python examples/pdf/ieee_builder.py

Outputs (under examples/out/):
  - ieee_sample.md
  - ieee_sample.pdf  (using IEEETemplate)
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easypour import Report, Table  # noqa: E402
from easypour.ieee import IEEETemplate  # noqa: E402


def _ensure_asset() -> pathlib.Path:
    assets = ROOT / "examples" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    png = assets / "layer_sparsity.png"
    if not png.exists():
        raise FileNotFoundError(
            f"Expected layer_sparsity.png under {assets}. Add a valid PNG before running this example."
        )
    return png


def build_report(asset_path: pathlib.Path) -> Report:
    """Construct a sample IEEE-style report with references, tables, and figures."""
    rpt = Report("Sample IEEE Paper", author="A. Researcher, B. Scientist")
    rpt.add_reference("smith19", 'J. Smith and R. Jones, "Neural Widgets," IEEE Trans., 2019.')
    rpt.add_reference("nguyen21", 'P. Nguyen, "Accelerating Edge Models," Proc. IEEE, 2021.')

    abstract = rpt.add_section("Abstract")
    abstract.add_text(
        "This sample demonstrates EasyPour's two-column PDF capabilities. "
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
        "EasyPour's `Report.write_pdf()` and `IEEETemplate`."
    )
    method.add_figure(
        asset_path,
        caption="Latency trend for the proposed system.",
        label="fig:latency",
        width="70%",
    )

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

    discussion = rpt.add_section("IV. Discussion")
    discussion.add_text(
        "Beyond raw metrics, we highlight qualitative feedback from reviewers:",
        "- Deployment pipeline shaved 25% off end-to-end startup time.",
        "- Model distillation maintained accuracy while shrinking memory usage.",
        "- Edge nodes benefit from the lower latency tail without infrastructure changes.",
    )
    discussion.add_text(
        "Future work includes deeper ablation studies, larger validation cohorts, and integrating "
        "hardware counters to track perf regressions in near real-time."
    )

    rpt.add_page_break()
    appendix = rpt.add_section("Appendix")
    appendix.add_text(
        "We include additional material beyond the main paper to illustrate how two-column layouts "
        "handle long-form content. Each subsection can cover implementation details, hyperparameter grids, "
        "or error analyses that would otherwise clutter the primary sections."
    )

    for idx in range(1, 4):
        appendix.add_section(f"Appendix Section {idx}").add_text(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Phasellus euismod, nisi a viverra lobortis, orci est gravida sapien, "
            "nec dictum turpis neque in leo. Fusce sed ultricies nunc. "
            "Aliquam erat volutpat. Pellentesque habitant morbi tristique senectus et netus.",
            "Curabitur et commodo est. Etiam id urna venenatis, sodales urna id, posuere massa. "
            "Maecenas suscipit, justo sed congue suscipit, arcu mi consequat mi, ac porta orci nisl vitae augue. "
            "Sed facilisis metus ac enim cursus, quis aliquet ante vulputate.",
        )

    rpt.ensure_references_section()
    return rpt


def main() -> None:
    """Build the IEEE sample report and write Markdown/PDF outputs."""
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
