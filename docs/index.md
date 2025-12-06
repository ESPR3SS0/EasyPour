---
title: EasyPour — Markdown Reports to HTML/PDF
---

# EasyPour

Turn tidy Python objects into Markdown, then to clean HTML and simple PDFs with a tiny, friendly API and a simple CLI.

Highlights
- Build a `Report` of nested `Section`s with text, `Table`s, and `Image`s.
- Render Markdown to HTML with tasteful defaults, or to PDF via ReportLab.
- Use from Python or the command line (`python -m easypour.cli`).

Features
- Streamlit integration: `Report.show_streamlit()` with configurable tabs and hooks
- Dash integration: `Report.to_dash_app()` to embed report HTML
- Interactive plots: `Section.add_matplotlib(..., interactive=True)` upgrades Matplotlib figures to Plotly in Streamlit/Dash without sacrificing PDF output
- Two-column PDF layout via `PDFTemplate(layout="two")` plus caption/numbering helpers (`add_figure`, `add_table(..., numbered=True)`)
- IEEE preset: `IEEETemplate` delivers ready-to-go Times fonts, two-column pages, and running headers.
- Cross references: label figures/tables (`label="fig:latency"`) and reuse them via `report.ref("fig:latency")`.
- Minimal surface area: easy to learn; extend via custom block renderers

Quick Links
- Getting Started: installation and a minimal example
- CLI: convert from Markdown or a Python builder
- Library API: `Report`, `Section`, `Table`, `Image`, helpers
- Rendering: HTML and PDF options, limitations
- Examples: simple, complex, Streamlit, Dash
- IEEE example: `python examples/pdf/ieee_builder.py`
- Troubleshooting and Contributing

Installation
- From source in this repo: `pip install .` (or editable: `pip install -e .`)
- PDF rendering uses ReportLab. Install if needed: `pip install reportlab`

Minimal Example
```python
from easypour import Report, Table, Image, b, i, code

rpt = Report(title="Weekly Model Analysis", author="ESPR3SS0", meta={"draft": True})
sec = rpt.add_section("Summary")
sec.add_text(
    f"This week was {b('great')} — latency down, accuracy steady.",
    f"We also verified {code('predict()')} on fresh data.",
)

metrics = Table(headers=["Metric", "Value"], rows=[["Accuracy", "92.8%"], ["F1", "91.5%"]])
rpt.add_section("Metrics").add_table(metrics)

rpt.add_section("Artifacts").add_image(Image("./charts/latency.png", alt="Latency", caption="P95 latency", width="60%"))

md = rpt.to_markdown()               # Markdown string (with front matter)
open("report.md", "w").write(md)

from easypour import markdown_to_html
open("report.html", "w").write(markdown_to_html(md, title=rpt.title))
rpt.write_pdf("report.pdf")
```

Why EasyPour?
- Small surface area, batteries included.
- Markdown first; HTML/PDF are just a render away.
- Friendly in scripts, notebooks, and CI.

Tip: To use the Material theme locally, install `mkdocs-material` and serve the docs:
- `pip install mkdocs-material`
- `mkdocs serve`
