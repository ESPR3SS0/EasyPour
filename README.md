# MochaFlow — Markdown Reports to HTML/PDF (with a smile)

Turn tidy Python objects into Markdown, then to beautiful HTML and PDF — all with a tiny, friendly API and a simple CLI.

## What Is It?
- Build a `Report` of nested `Section`s with text, `Table`s, and `Image`s.
- Render Markdown to HTML with tasteful defaults, or to PDF via ReportLab.
- Drive it from Python or from the command line using `python -m mochaflow.cli`.

## Install
Pick one of the options below.

- From PyPI (if/when published):
  - `pip install MochaFlow`
- Include optional WeasyPrint dependency (for Markdown→PDF via CLI):
  - `pip install "MochaFlow[weasy]"`
- From source (this repo):
  - `pip install .`  (or editable: `pip install -e .`)

PDF rendering uses ReportLab (pure Python wheels available on PyPI). If you don’t already have it: `pip install reportlab`.

## Quick Start (Library)
Create a small report, write Markdown, and export HTML/PDF.

```python
from mochaflow import Report, Table, Image, b, i, code

# Build a report
rpt = Report(title="Weekly Model Analysis", author="ESPR3SS0", meta={"draft": True})
sec = rpt.add_section("Summary")
sec.add_text(
    f"This week was {b('great')} — latency down, accuracy steady.",
    f"We also verified {code('predict()')} on fresh data.",
)

# Add a table
metrics = Table(headers=["Metric", "Value"], rows=[["Accuracy", "92.8%"], ["F1", "91.5%"]])
rpt.add_section("Metrics").add_table(metrics)

# Add an image (caption and width use a <figure> wrapper)
rpt.add_section("Artifacts").add_image(Image("./charts/latency.png", alt="Latency", caption="P95 latency", width="60%"))

# Write Markdown
md_path = rpt.write_markdown("report.md")
print("Wrote:", md_path)

# Render to HTML (inline CSS included)
from mochaflow import markdown_to_html
html = markdown_to_html(rpt.to_markdown(), title=rpt.title)
open("report.html", "w", encoding="utf-8").write(html)

# Render to PDF (ReportLab backend)
rpt.write_pdf("report.pdf")

# Configure PDF defaults in code (page size, margins, fonts, captions)
rpt.configure_pdf(
    page_size=(8.5 * 72, 11 * 72),
    margins=(54, 54, 72, 72),
    layout="two",
    column_gap=22,
    font="Times-Roman",
    figure_caption_style={"font": "Times-Italic"},
)
rpt.write_pdf("report_two_col.pdf")

# Use the IEEE preset for two-column output (optional)
from mochaflow.ieee import IEEETemplate
rpt.write_pdf("report_ieee.pdf", template=IEEETemplate())
```

## Quick Start (CLI)
You can also use the CLI module.

- From an existing Markdown file to HTML/PDF (PDF requires `MochaFlow[weasy]`):
  - `python -m mochaflow.cli --from-md report.md --html report.html`
  - `python -m mochaflow.cli --from-md report.md --pdf report.pdf`
- From a Python builder to Markdown/HTML/PDF:
  1) Create `builder.py` with a `build_report()` function that returns either a `Report` or a Markdown `str`:
     ```python
     # builder.py
     from mochaflow import Report
     def build_report():
         r = Report("CLI Report", author="You")
         r.add_section("Hello").add_text("This was generated via the CLI.")
         return r
     ```
  2) Run it:
     - Markdown: `python -m mochaflow.cli --builder builder.py --md out.md`
     - HTML: `python -m mochaflow.cli --builder builder.py --html out.html`
     - PDF (requires `build_report()` to return a `Report`): `python -m mochaflow.cli --builder builder.py --pdf out.pdf`

Tip: `--builder` and `--from-md` are mutually exclusive.

## Little Things That Delight
- Inline helpers: `b("bold")`, `i("italic")`, `u("underline")`, `code("snippet")`, `link("text", "https://…")`.
- Tables: `Table.from_dicts([{...}, {...}])` or explicit headers/rows.
- Images: pass `caption` and/or `width` (like `"60%"` or `"380px"`) for a `<figure>` wrapper.
- Math snippets: `Section.add_math(r"\int_0^1 ...", caption="Integral")` renders TeX-like formulas via matplotlib.
- Figures/tables with numbering: `Section.add_figure(...)` / `Section.add_table(..., numbered=True)` auto-generate IEEE-style captions.
- Citations: `Report.add_reference(...)` + `report.cite("smith19")` give you `[1]` references and an auto-built References section.
- Layout control: `PDFTemplate(layout="two", column_gap=24)` or even `template.register_layout("cover", builder)` let you define single/two/custom column frames and caption styles without touching ReportLab internals.
- Global PDF tuning without templates: `report.configure_pdf(page_size=..., margins=..., font="Times-Roman", header_fn=...)` sets default page size, margins, fonts, column layouts, headers/footers, and caption styles. If you also pass a custom template, MochaFlow will warn when your code-level choices override template values so you always know which settings win.
- Interactive plots: `Section.add_matplotlib(fig, interactive=True)` keeps the PDF static while upgrading the Streamlit/Dash view to Plotly (zoom/pan/hover).
- Cross references: Label figures/tables (`label="fig:latency"`) and drop `report.ref("fig:latency")` anywhere to emit `Figure N`.
- Sensible HTML defaults: readable fonts, clean tables, page numbers for PDF.
- Extra styling: `markdown_to_html(md, extra_css="body { color: #333; }")` or pass a custom `PDFTemplate` to `Report.write_pdf`.

## Why MochaFlow?
- Small surface area, batteries included.
- Markdown first; HTML/PDF are just a render away.
- Works great in scripts, notebooks, and CI.

## Troubleshooting
- PDF export fails or looks odd:
  - Ensure ReportLab is installed: `pip install reportlab`.
  - Check that any referenced images exist on disk and are reachable from your working directory.
- CLI says the builder is missing:
  - Your `builder.py` must define `build_report()`.

## Contributing & Tests
- Run all tests: `pytest -q`
- Quick, no-PDF/CLI tests: `pytest -q -m "not pdf and not cli"`
- Lint/format: `ruff check .` and `ruff format .`

Enjoy making many marks! ✨

## More Examples

All examples below are pure Python — you can drop them in a `builder.py` and run them via the CLI too.

### Bullets, Checklists, Code Blocks, Strikethrough

```python
from mochaflow.core import Report

r = Report("Lists + Code")
s = r.add_section("Goodies")
s.add_bullets(["Item A", "Item B", "Item C"])           # - bullets
s.add_checklist([("Do A", False), ("Done B", True)])      # - [ ] / [x]
s.add_codeblock("print('hello world')", language="python") # ```python
s.add_strikethrough("old text")                            # ~~old text~~

open("lists.md", "w").write(r.to_markdown())
```

### Tables (from dicts) and Images (by path)

```python
from mochaflow.core import Report, Table

r = Report("Data + Image")
data = [
    {"Metric": "Accuracy", "Value": "92.8%"},
    {"Metric": "F1",       "Value": "91.5%"},
]
r.add_section("Results").add_table(Table.from_dicts(data))
r.add_section("Plot").add_image_path("./charts/acc.png", alt="acc", caption="Accuracy", width="50%")
```

### Matplotlib → Image (inline convenience)

```python
from mochaflow.core import Report
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(3, 2))
ax.plot([0, 1, 2], [0, 1, 0])
ax.set_title("Curve")

r = Report("Matplotlib Demo")
r.add_section("Figure").add_matplotlib(fig, out_dir="assets", filename="curve.png", caption="A curve", width="60%")

r.write_pdf("mpl.pdf")
```

### Two-Column Layout + References

```python
from mochaflow import Report
from mochaflow.core import Table
from mochaflow.render import PDFTemplate

r = Report("Two-Column Demo", author="MochaFlow Labs")
r.add_reference("smith19", "Smith et al., 'Cool Paper', IEEE, 2019.")

sec = r.add_section("Results")
sec.add_text(
    f"This result improves latency by 20% {r.cite('smith19')} as illustrated in {r.ref('fig:latency')}."
)
sec.add_table(
    Table(headers=["Metric", "Value"], rows=[["Latency", "12ms"], ["AUC", "0.962"]]),
    caption="Key performance metrics",
    numbered=True,
    label="tab:metrics",
)
fig_sec = r.add_section("Figures")
fig_sec.add_figure("./charts/latency.png", caption="Latency over input rate", label="fig:latency", width="60%")

r.ensure_references_section()

template = PDFTemplate(layout="two", column_gap=24)
r.write_pdf("two_column.pdf", template=template)
```
Use `r.ref("fig:latency")` (or any label you assign) anywhere in your narrative to produce the resolved text (e.g., `Figure 1`), keeping captions and references consistent across Markdown, HTML, PDF, Streamlit, and Dash.

### Math Formulas → Image

```python
from mochaflow.core import Report

r = Report("Math Demo")
sec = r.add_section("Equations")
sec.add_math(r"\int_0^1 x^2\,dx = \frac{1}{3}", caption="Simple integral", width="220px")

r.write_pdf("math.pdf")
```

### IEEE-Style Sample

```bash
python examples/pdf/ieee_builder.py
```

Generates Markdown and an IEEE-style PDF (two columns, captions, references) in `examples/out/` using `IEEETemplate`.

### Simple Full Workflow (Markdown + PDF + Streamlit/Dash)

- Generate Markdown/PDF: `python examples/playbook/simple_full.py`
- Preview in Streamlit: `streamlit run examples/playbook/simple_full.py -- --preview streamlit`
- Preview in Dash: `python examples/playbook/simple_full.py --preview dash`

### Advanced Full Workflow (IEEE template + interactive figures)

- Generate Markdown/PDF: `python examples/playbook/advanced_full.py`
- Preview in Streamlit: `streamlit run examples/playbook/advanced_full.py -- --preview streamlit`
- Preview in Dash: `python examples/playbook/advanced_full.py --preview dash`

### Streamlit Example

Run an interactive Streamlit app that builds a report, previews Markdown/HTML, and lets you download a PDF.

- Command: `streamlit run examples/streamlit/app.py`
- Minimal gist:

```python
# examples/streamlit/app.py (excerpt)
import streamlit as st
from mochaflow.core import Report, Table
from mochaflow import markdown_to_html

def build_report(include_table: bool) -> Report:
    rpt = Report("Streamlit Demo", author="Examples")
    rpt.add_section("Summary").add_text("Generated inside Streamlit.")
    if include_table:
        rpt.add_section("Metrics").add_table(Table.from_dicts([
            {"Metric": "Accuracy", "Value": "92.8%"},
            {"Metric": "F1", "Value": "91.5%"},
        ]))
    return rpt

st.sidebar.header("Options")
opt_table = st.sidebar.checkbox("Include table", value=True)
rpt = build_report(opt_table)
md = rpt.to_markdown()
st.code(md, language="markdown")
html = markdown_to_html(md, title=rpt.title)
st.components.v1.html(html, height=400, scrolling=True)
```

Tip: `Report.show_streamlit()` now defaults to four tabs—`Report` (native Streamlit rendering), `Markdown`, `HTML`, and `PDF` (download button)—and you can reorder or trim them via `configure_streamlit(tabs=[...])`.

### Streamlit Interactive Plots Example

- Command: `streamlit run examples/streamlit/interactive_plots.py`
- Demonstrates how `Section.add_matplotlib(fig, interactive=True, ...)` preserves the static PNG for Markdown/PDF while automatically upgrading the Streamlit view to Plotly charts (zoom, pan, hover).

### Dash Example

Run a Dash app that renders the report HTML inside the app.

- Command: `python examples/dash/app.py` then open http://127.0.0.1:8050/
- Minimal gist:

```python
# examples/dash/app.py (excerpt)
from dash import Dash, dcc, html, Input, Output
from mochaflow.core import Report, Table
from mochaflow import markdown_to_html

def build_report(include_table: bool) -> Report:
    r = Report("Dash Demo", author="Examples")
    r.add_section("Summary").add_text("Generated inside Dash.")
    if include_table:
        r.add_section("Metrics").add_table(Table.from_dicts([
            {"Metric": "Accuracy", "Value": "92.8%"},
            {"Metric": "F1", "Value": "91.5%"},
        ]))
    return r

app = Dash(__name__)
app.layout = html.Div([
    dcc.Checklist(id="opts", options=[{"label": "Include table", "value": "table"}], value=["table"]),
    html.Div(id="content"),
])

@app.callback(Output("content", "children"), [Input("opts", "value")])
def update_content(values):
    rpt = build_report("table" in (values or []))
    html_doc = markdown_to_html(rpt.to_markdown(), title=rpt.title)
    return html.Iframe(srcDoc=html_doc, style={"width": "100%", "height": "70vh"})
```

Tip: Dash apps created via `report.to_dash_app()` default to tabs for `Report`, `Markdown`, `HTML`, and `PDF` (download button powered by ReportLab). Customize the subset/order with `report.configure_dash(tabs=["Report", "PDF"])`, or add your own layout around the returned Dash app.

### Dash Interactive Plots Example

- Command: `python examples/dash/interactive_plots.py`
- Mirrors the Streamlit demo but inside Dash: Matplotlib figures remain PNGs in Markdown/PDF yet show up as fully interactive Plotly graphs in the Dash app.
