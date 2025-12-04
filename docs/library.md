---
title: Library API
---

# Library API

Core Types
- `Report(title, author=None, date_str=None, meta=None)`
  - `add_section(title) -> Section`: append a new top-level section (H2)
  - `to_markdown() -> str`: YAML front matter + document body
  - `write_markdown(path) -> str`: write Markdown and return absolute path
  - `write_pdf(path, template=None) -> str`: render this report directly to PDF (ReportLab)
  - `configure_pdf(**options) -> Report`: set PDF defaults (page size, margins, fonts, layout, column gap, header/footer callables, caption styles) without instantiating `PDFTemplate` manually. When a template is also supplied to `write_pdf()`, these code-level choices take precedence and emit a warning whenever they override a value from the provided template.
- `Section(title, level=2)`
  - `add_text(*paragraphs) -> Section`: add one or more paragraphs
  - `add_table(Table) -> Section`
  - `add_image(Image, label=None, numbered=False) -> Section`
  - `add_image_path(path, alt='', caption=None, width=None, label=None, numbered=False) -> Section`
  - `add_figure(path, caption=None, label=None, width=None, alt='') -> Section`
  - `add_section(title) -> Section`: nested section (level increases, clamped to H6)
  - Lists/Code helpers:
    - `add_bullets(items: Iterable[str])`
    - `add_checklist(items: Iterable[tuple[str, bool]])`
    - `add_codeblock(code_text: str, language: str | None = None)` (handles backticks inside code)
    - `add_strikethrough(text: str)`
    - `add_math(formula, out_dir=".mochaflow_math", dpi=220, caption=None, width=None, alt=None)`
    - `add_matplotlib(obj, out_dir=None, filename=None, alt='', caption=None, width=None, dpi=180, interactive=False, label=None, numbered=True)`
      - Saves a PNG for Markdown/PDF; with `interactive=True` (and Plotly installed) the same figure becomes an interactive chart inside Streamlit/Dash automatically.
- `Table(headers: list[str], rows: list[list[str|int|float]])`
  - `from_dicts(rows: Iterable[dict[str, Any]]) -> Table`
  - `to_markdown() -> str`
- `Image(path, alt='', caption=None, width=None)`
  - `to_markdown() -> str` (uses `<figure>` wrapper if `caption` or `width` is provided)

Inline Helpers
- `bold(text)` / alias `b(text)` -> `**text**`
- `italic(text)` / alias `i(text)` -> `*text*`
- `underline(text)` / alias `u(text)` -> `<u>text</u>` (HTML for portability)
- `code(text)` -> `` `text` ``
- `url(text, url)` / alias `link(text, url)` -> `[text](url)`

Rendering Helpers
- `markdown_to_html(md_text, title='Report', extra_css=None) -> str`
  - CommonMark + tables + strikethrough; ships with inline default CSS
  - `extra_css` is appended to the default stylesheet
- `Report.write_pdf(path, template=None) -> str`
  - ReportLab renderer operating on the structured `Report`
  - Pass a custom `PDFTemplate` (from `mochaflow.render`) to tweak fonts, margins, or colors
- `tex_to_png(formula, out_dir, dpi=220) -> Path`
  - Lazily import the math renderer (matplotlib mathtext) to convert TeX-like strings into tightly cropped PNGs
- `Report.add_reference(key, entry)`, `Report.cite(key) -> str`, `Report.ensure_references_section(title="References")`
  - Track IEEE-style numeric citations and automatically build a references section ordered by first use
- `Report.ref(label, default=None) -> str`
  - Reference labeled figures/tables anywhere in your narrative (e.g., returns `"Figure 2"`)
- `PDFTemplate.register_layout(name, builder)`
  - Supply a custom layout that returns a list of ReportLab `Frame`s; use via `layout="name"` or `first_page_layout="name"` for per-page control

Interactive Previews
- `Report.show_streamlit(height=420)`
  - Shows tabs for a native “Report” view, raw Markdown, HTML preview, and a PDF download button (when ReportLab is installed).
  - Run your script with `streamlit run script.py` and call `report.show_streamlit()`.
- `Report.to_dash_app()`
  - Returns a minimal Dash app that renders the report HTML; run with `app.run_server()`.

Streamlit Customization
- `Report.configure_streamlit(**options)`
  - Supported keys: `page_title`, `layout` ("wide" or "centered"), `height` (HTML tab height),
    `tabs` (subset/order of ["Report", "Markdown", "HTML", "PDF"]).
- `Report.set_streamlit_hooks(sidebar=None, before_render=None, after_render=None)`
  - Register callbacks receiving `(st, report)` that can mutate UI/state:
    - `sidebar`: executed inside `st.sidebar` before rendering
    - `before_render`: executed after title/caption, before tabs
    - `after_render`: executed after all tabs are rendered
- `Report.register_streamlit_renderer(block_type, renderer)`
  - Supply a custom renderer for a block type; `renderer(st, block, report)` should emit Streamlit widgets.
- `Report.st` (property)
  - Access the `streamlit` module instance used by `show_streamlit()` for ad‑hoc customization.

Example: customize sidebar and tabs
```python
from mochaflow import Report

def sidebar(st, report):
    st.checkbox("Extra toggle", key="extra")

r = Report("Demo").configure_streamlit(tabs=["Report", "Markdown", "PDF"], page_title="Custom Title")
r.set_streamlit_hooks(sidebar=sidebar)
r.show_streamlit()
```

Interactive Matplotlib (Streamlit/Dash)
- `Section.add_matplotlib(fig_or_axes, interactive=True, ...)`
  - Saves a PNG for Markdown/PDF, and when Plotly is installed the same figure is converted to an interactive chart (zoom/pan/hover) in Streamlit/Dash automatically.
  - If Plotly is unavailable, the block gracefully falls back to the static image everywhere.

Front Matter
- `Report.to_markdown()` emits YAML front matter with `title`, optional `author`, `date` and any `meta` items you provide.

Levels and Nesting
- `Section.add_section()` increases heading level and clamps at H6 to keep valid Markdown structure.

Matplotlib Convenience
- `Section.add_matplotlib(fig_or_axes, ...)` saves a PNG and adds as an `Image` block.
- Defaults to a local directory `.mochaflow_figs/` if `out_dir` is not provided.

Example
```python
from mochaflow import Report, Table, Image, bold, code

r = Report("Demo", author="You")
r.add_section("Summary").add_text(
    f"This is {bold('important')} and uses {code('inline')} code."
)
r.add_section("Metrics").add_table(Table.from_dicts([
    {"Metric": "Accuracy", "Value": "92.8%"},
    {"Metric": "F1", "Value": "91.5%"},
]))
r.add_section("Artifacts").add_image(Image("chart.png", alt="Chart", caption="Model curve", width="60%"))
md = r.to_markdown()
```
