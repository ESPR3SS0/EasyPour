---
title: Getting Started
---

# Getting Started

Install
- From source (this repo): `pip install .`
- Editable for development: `pip install -e .`
- PDF support: `pip install reportlab`

Optional Extras
- Matplotlib for `Section.add_matplotlib(...)` and `Section.add_math(...)`: `pip install matplotlib`
- Streamlit example: `pip install streamlit`
- Dash example: `pip install dash`

Hello, Report
```python
from pourover import Report, Table

rpt = Report("Hello Report", author="You")
rpt.add_section("Summary").add_text("This is a very small report.")
rpt.add_section("Metrics").add_table(Table(headers=["A", "B"], rows=[[1, 2], [3, 4]]))

md = rpt.to_markdown()
open("report.md", "w", encoding="utf-8").write(md)
```

Render to HTML
```python
from pourover import markdown_to_html
html = markdown_to_html(md, title=rpt.title)
open("report.html", "w", encoding="utf-8").write(html)
```

Render to PDF (ReportLab backend)
```python
rpt.write_pdf("report.pdf")
```

Instant Streamlit Preview
```python
# my_app.py
from pourover import Report, Table

r = Report("Preview Me", author="You")
r.add_section("Hello").add_text("This is shown in Streamlit.")
r.add_section("Metrics").add_table(Table(headers=["A","B"], rows=[[1,2],[3,4]]))
r.show_streamlit()
# Run: streamlit run my_app.py
```

Minimal Dash App
```python
# app.py
from pourover import Report

r = Report("Dash Preview")
r.add_section("Hello").add_text("Rendered in a minimal Dash app.")
app = r.to_dash_app()
app.run_server(debug=True)
```

CLI Basics
- From Markdown to HTML/PDF (PDF requires `PourOver[weasy]`):
  - `python -m pourover.cli --from-md report.md --html report.html`
  - `python -m pourover.cli --from-md report.md --pdf report.pdf`
- From a Python builder to outputs (including ReportLab-backed PDF): see the CLI page.

## End-to-End Workflow (Artifacts + Previews)

While the snippets above cover the core API, the repository also ships ready-to-run playbooks that generate Markdown/PDF and optionally preview the same report in Streamlit or Dash. These scripts are ideal when you want to hand stakeholders a PDF but also show the results in a lightweight dashboard.

### Simple Report (examples/playbook/simple_full.py)

1. **Generate artifacts**
   ```bash
   python examples/playbook/simple_full.py
   # -> examples/out/simple_full.md
   # -> examples/out/simple_full.pdf
   ```
2. **Preview in Streamlit**
   ```bash
   streamlit run examples/playbook/simple_full.py -- --preview streamlit
   ```
3. **Preview in Dash**
   ```bash
   python examples/playbook/simple_full.py --preview dash
   ```
   Both previews reuse the *same* `Report`: Streamlit calls `report.show_streamlit()` (tabs for Report/Markdown/HTML/PDF) and Dash wraps `report.to_dash_app()` with minimal boilerplate.

### Advanced Report (examples/playbook/advanced_full.py)

1. **Generate artifacts with the IEEE template**
   ```bash
   python examples/playbook/advanced_full.py
   # -> examples/out/advanced_full.md
   # -> examples/out/advanced_full.pdf
   ```
2. **Preview interactively**
   ```bash
   streamlit run examples/playbook/advanced_full.py -- --preview streamlit
   python examples/playbook/advanced_full.py --preview dash
   ```
   The advanced script showcases references (`report.ref("fig:latency")`), numbered tables, interactive figures, and the `IEEETemplate`.

## References and Labels

Any figure/table can be labeled and later referenced in prose:

```python
sec.add_matplotlib(fig, caption="Latency", label="fig:latency", numbered=True)
sec.add_table(tbl, caption="KPIs", label="tab:metrics", numbered=True)
sec.add_text(
    f"See {report.ref('fig:latency')} for the trend and {report.ref('tab:metrics')} for the KPI snapshot."
)
```

PourOver keeps the numbering consistent in Markdown, PDF, Streamlit, and Dash. If a label does not exist, `report.ref()` raises a `KeyError` (or returns the optional `default=` string).

## Interactive Figures

`Section.add_matplotlib(..., interactive=True)` saves the Matplotlib figure for Markdown/PDF, but when Plotly is installed the Streamlit and Dash renderers automatically upgrade the figure to a Plotly chart (zoom/pan/hover) without extra UI code.

- **Static artifacts** (Markdown/PDF) still receive the PNG and caption.
- **Streamlit/Dash** show an interactive chart inside the Report tab.

Try it yourself:

```bash
streamlit run examples/streamlit/interactive_plots.py
python examples/dash/interactive_plots.py
```

Next Steps
- Learn the core library on the Library API page
- See rendering options on the Rendering page
- Explore ready-made examples on the Examples page
