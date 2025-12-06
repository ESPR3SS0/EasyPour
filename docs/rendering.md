---
title: Rendering
---

# Rendering

HTML
- `markdown_to_html(md_text, title='Report', extra_css=None) -> str`
- Uses Markdown-It (CommonMark) with tables, strikethrough, and linkify enabled.
- Ships with sensible inline CSS for typography, tables, figures.
- You can append styles via `extra_css`.

PDF (ReportLab)
- `Report.write_pdf(path, template=None) -> str` uses the ReportLab backend on the structured `Report`.
- `PDFTemplate` in `easypour.render` provides tunable defaults (page size, fonts, colors, spacing) and can switch to automatic two-column pages by setting `layout="two"` and adjusting `column_gap`.
- Want to tweak those defaults without touching templates? Call `report.configure_pdf(page_size=..., margins=(...), font="Times-Roman", header_fn=...)` before `write_pdf()`. Those code-level overrides win over template settings, and if you pass a custom template EasyPour emits a warning so you know which value takes precedence.
- Figures (`Section.add_figure` or `add_image(..., numbered=True)`) and tables (`add_table(..., caption=..., numbered=True)`) receive IEEE-style captions and numbering. Labels can be assigned and collected for custom cross-references.
- Images referenced via `Image`/`add_image_path` are resolved directly from the filesystem; ensure the assets exist relative to your working directory.
- Need a custom layout (single-column cover page, three-column appendix, etc.)? Call `PDFTemplate.register_layout("name", builder)` with a callable that returns a list of ReportLab `Frame`s, then set `layout="name"` or `first_page_layout="name"`. Caption prefixes and styles are configurable via `figure_prefix`, `table_prefix`, `figure_caption_style`, and `table_caption_style`.

Preset templates
- `IEEETemplate` in `easypour.ieee` builds on `PDFTemplate` with Times fonts, single-column cover page, two-column body, and running headers/page numbers tuned for IEEE conference papers. Use it directly: `report.write_pdf("paper.pdf", template=IEEETemplate())`.

Default HTML Styles
The HTML renderer injects a small default stylesheet focused on readability:
- System fonts for text and UI-monospace for code
- Clean table borders and padding
- Figure/caption support via `<figure>` and `<figcaption>`

Example
```python
from easypour import markdown_to_html

html = markdown_to_html(md, title="My Report", extra_css="body { color: #333; }")
```

Object‑driven PDF example
```python
from easypour.core import Report, Table
from easypour.render import PDFTemplate

rpt = Report("Object Export")
rpt.add_section("Metrics").add_table(
    Table.from_dicts([
        {"Metric": "Accuracy", "Value": "92.8%"},
        {"Metric": "F1", "Value": "91.5%"},
    ]),
    caption="Validation metrics",
    numbered=True,
)
tpl = PDFTemplate(layout="two", column_gap=24)
rpt.write_pdf("out_obj.pdf", template=tpl)
```
