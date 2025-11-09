from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Dict, List, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    KeepInFrame,
    Image as RLImage,
    PageBreak as RLPageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table as RLTable,
    TableStyle,
)

from .core import (
    DFInteractivePlot,
    DataFrameBlock,
    Image as CoreImage,
    PageBreak as CorePageBreak,
    Report,
    Section,
    Table as CoreTable,
)
from .inline import parse_inline
from .pdfmixins import (
    AbsoluteImageDirective,
    DoubleSpaceDirective,
    FlowableDirective,
    FloatingImageDirective,
    TwoColumnDirective,
    VerticalSpaceDirective,
)

__all__ = [
    "PDFTemplate",
    "report_to_pdf",
    "markdown_to_html",
    "markdown_to_pdf",
]


Alignment = {
    "left": TA_LEFT,
    "center": TA_CENTER,
    "right": TA_RIGHT,
    "justify": TA_JUSTIFY,
}


@dataclass
class PDFTemplate:
    page_size: Sequence[float] = letter
    margin_left: float = 54
    margin_right: float = 54
    margin_top: float = 64
    margin_bottom: float = 64
    layout: str = "single"

    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    mono_font: str = "Courier"
    base_font_size: float = 10.5
    h1: float = 20
    h2: float = 16
    h3: float = 13
    line_spacing: float = 1.2

    text_color: Any = colors.black
    accent_color: Any = colors.HexColor("#2b6cb0")
    table_header_bg: Any = colors.HexColor("#efefef")
    table_header_text: Any = colors.black

    header_fn: Optional[Callable[[canvas.Canvas, "PDFTemplate", int], None]] = None
    footer_fn: Optional[Callable[[canvas.Canvas, "PDFTemplate", int], None]] = None

    def make_document(self, output: str) -> SimpleDocTemplate:
        doc = SimpleDocTemplate(
            output,
            pagesize=self.page_size,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
        )
        return doc


class DashboardMixin:
    """Deprecated stub left in place for backwards compatibility."""

    def show_as_streamlit(self):  # pragma: no cover - legacy stub
        raise NotImplementedError("DashboardMixin is deprecated; use Report.show_streamlit().")

    def show_as_dash(self):  # pragma: no cover - legacy stub
        raise NotImplementedError("DashboardMixin is deprecated; use Report.to_dash_app().")


def _color(value: Any):
    if isinstance(value, str):
        if value.startswith("#"):
            return colors.HexColor(value)
        try:
            return colors.getNamedColor(value)
        except Exception:
            return colors.black
    return value


def _paragraph_style(
    template: PDFTemplate,
    *,
    overrides: Optional[Dict[str, Any]] = None,
    base_font: Optional[str] = None,
    font_size: Optional[float] = None,
) -> ParagraphStyle:
    overrides = overrides or {}
    font_name = overrides.get("font") or overrides.get("font_name") or base_font or template.font
    size = overrides.get("font_size") or font_size or template.base_font_size
    leading = overrides.get("leading") or (size * template.line_spacing)
    alignment_name = str(overrides.get("alignment", "left")).lower()
    alignment = Alignment.get(alignment_name, TA_LEFT)
    color_value = overrides.get("color") or overrides.get("text_color") or template.text_color
    style = ParagraphStyle(
        name=f"style_{id(overrides)}",
        fontName=font_name,
        fontSize=size,
        leading=leading,
        textColor=_color(color_value),
        alignment=alignment,
        spaceBefore=overrides.get("space_before", 0),
        spaceAfter=overrides.get("space_after", 0),
    )
    return style


def _escape(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    return text


def _inline_to_html(text: str, template: PDFTemplate) -> str:
    runs = parse_inline(text)
    pieces: List[str] = []
    for run in runs:
        frag = _escape(run.text)
        if not frag and run.footnote_key:
            frag = _escape(run.footnote_key)
        if run.code:
            frag = f'<font face="{template.mono_font}">{frag}</font>'
        if run.underline:
            frag = f"<u>{frag}</u>"
        if run.italic:
            frag = f"<i>{frag}</i>"
        if run.bold:
            frag = f"<b>{frag}</b>"
        if run.link:
            frag = f'<link href="{run.link}">{frag}</link>'
        if run.footnote_key:
            frag = f"<super>{frag}</super>"
        pieces.append(frag)
    return "".join(pieces) if pieces else _escape(text)


def _paragraph(text: str, template: PDFTemplate, overrides: Optional[Dict[str, Any]] = None) -> Paragraph:
    style = _paragraph_style(template, overrides=overrides)
    html = _inline_to_html(text, template)
    return Paragraph(html, style)


def _heading(text: str, level: int, template: PDFTemplate, overrides: Optional[Dict[str, Any]] = None) -> Paragraph:
    sizes = {1: template.h1, 2: template.h2, 3: template.h3}
    font_size = sizes.get(level, max(template.base_font_size, template.base_font_size + 2 - (level - 3)))
    style = _paragraph_style(
        template,
        overrides=overrides,
        base_font=template.font_bold,
        font_size=font_size,
    )
    return Paragraph(_inline_to_html(text, template), style)


def _table(block: CoreTable, template: PDFTemplate) -> RLTable:
    data = [block.headers] + block.rows
    style_opts = block.pdf_style or {}
    col_widths = style_opts.get("col_widths")
    row_heights = style_opts.get("row_heights")
    table = RLTable(data, colWidths=col_widths, rowHeights=row_heights, repeatRows=1)
    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), _color(style_opts.get("header_bg", template.table_header_bg))),
        ("TEXTCOLOR", (0, 0), (-1, 0), _color(style_opts.get("header_text", template.table_header_text))),
        ("FONTNAME", (0, 0), (-1, 0), style_opts.get("header_font", template.font_bold)),
        ("FONTNAME", (0, 1), (-1, -1), style_opts.get("body_font", template.font)),
        ("FONTSIZE", (0, 0), (-1, -1), style_opts.get("font_size", template.base_font_size)),
        ("ALIGN", (0, 0), (-1, -1), style_opts.get("align", "LEFT")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), style_opts.get("grid_width", 0.25), _color(style_opts.get("grid_color", colors.grey))),
    ]
    if "style" in style_opts:
        base_style.extend(style_opts["style"])
    table.setStyle(TableStyle(base_style))
    return table


def _image(block: CoreImage, template: PDFTemplate) -> List[Any]:
    flowables: List[Any] = []
    path = block.path
    width = block.pdf_style.get("width") if block.pdf_style else None
    height = block.pdf_style.get("height") if block.pdf_style else None
    if width is None and isinstance(block.width, int):
        width = block.width
    img = RLImage(path, width=width, height=height)
    flowables.append(img)
    if block.caption:
        flowables.append(Spacer(1, template.base_font_size * 0.2))
        cap_style = block.pdf_style.get("caption_style") if block.pdf_style else {"font_size": template.base_font_size - 1, "color": colors.grey}
        flowables.append(_paragraph(block.caption, template, overrides=cap_style))
    return flowables


class _AbsoluteImageFlowable(Flowable):
    def __init__(self, directive: AbsoluteImageDirective):
        super().__init__()
        self.directive = directive
        self._reader = ImageReader(directive.path)

    def wrap(self, *_) -> tuple[float, float]:  # pragma: no cover - positional flowable
        return (0, 0)

    def draw(self) -> None:  # pragma: no cover - ReportLab callback
        canv = self.canv
        width, height = self._reader.getSize()
        dw = self.directive.width or width
        dh = self.directive.height or height
        canv.saveState()
        canv.drawImage(
            self.directive.path,
            self.directive.x,
            self.directive.y,
            width=dw,
            height=dh,
            mask="auto",
        )
        canv.restoreState()


def _floating_image(block: FloatingImageDirective, template: PDFTemplate) -> List[Any]:
    img = RLImage(block.path, width=block.width, height=block.height)
    align = block.align.lower()
    if align == "right":
        img.hAlign = "RIGHT"
    elif align == "center":
        img.hAlign = "CENTER"
    else:
        img.hAlign = "LEFT"
    flows: List[Any] = [img]
    if block.caption:
        flows.append(Spacer(1, block.padding))
        flows.append(
            _paragraph(
                block.caption,
                template,
                overrides={"alignment": align if align in {"left", "right", "center"} else "left", "color": colors.grey},
            )
        )
    flows.append(Spacer(1, block.padding))
    return flows


def _two_column_flowables(block: TwoColumnDirective, template: PDFTemplate) -> List[Any]:
    left = []
    right = []
    for item in block.left:
        left.extend(_block_flowables(item, template))
    for item in block.right:
        right.extend(_block_flowables(item, template))
    usable = template.page_size[0] - template.margin_left - template.margin_right
    gap = block.gap
    col_width = max(10.0, (usable - gap) / 2)
    def _column(content: List[Any]) -> KeepInFrame:
        items = content or [Spacer(1, 0)]
        return KeepInFrame(col_width, 10_000, items, mode="shrink", mergeSpace=True)

    table = RLTable(
        [[_column(left), _column(right)]],
        colWidths=[col_width, col_width],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (1, 0), (1, 0), gap / 2),
                ("RIGHTPADDING", (0, 0), (0, 0), gap / 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [table]


def _render_dataframe(block: DataFrameBlock, template: PDFTemplate) -> List[Any]:
    try:
        import pandas as pd  # type: ignore

        if hasattr(block.data, "columns"):
            df = block.data
        else:
            df = pd.DataFrame(block.data)
        headers = list(df.columns)
        rows = df.values.tolist()
        tbl = _table(CoreTable(headers=headers, rows=rows), template)
        flows: List[Any] = [tbl]
        if block.caption:
            flows.append(Spacer(1, template.base_font_size * 0.2))
            flows.append(_paragraph(block.caption, template, {"alignment": "center", "color": colors.grey}))
        return flows
    except Exception:
        return [_paragraph(block.caption or "(DataFrame unavailable)", template)]


def _block_flowables(block: Any, template: PDFTemplate) -> List[Any]:
    flows: List[Any] = []
    if isinstance(block, str):
        flows.append(_paragraph(block, template))
    elif isinstance(block, CoreTable):
        flows.append(_table(block, template))
    elif isinstance(block, CoreImage):
        flows.extend(_image(block, template))
    elif isinstance(block, DFInteractivePlot):
        note = block.title or "Interactive plot (view in Streamlit)"
        flows.append(_paragraph(note, template))
    elif isinstance(block, CorePageBreak):
        flows.append(RLPageBreak())
    elif isinstance(block, DataFrameBlock):
        flows.extend(_render_dataframe(block, template))
    elif isinstance(block, Section):
        flows.extend(_render_section(block, template))
    elif isinstance(block, FlowableDirective):
        produced = block.factory(template)
        if produced is not None:
            if isinstance(produced, (list, tuple)):
                for item in produced:
                    if item is not None:
                        flows.append(item)
            else:
                flows.append(produced)
    elif isinstance(block, TwoColumnDirective):
        flows.extend(_two_column_flowables(block, template))
    elif isinstance(block, AbsoluteImageDirective):
        flows.append(_AbsoluteImageFlowable(block))
    elif isinstance(block, FloatingImageDirective):
        flows.extend(_floating_image(block, template))
    elif isinstance(block, VerticalSpaceDirective):
        flows.append(Spacer(1, block.height))
    elif isinstance(block, DoubleSpaceDirective):
        if block.active:
            flows.append(Spacer(1, template.base_font_size * template.line_spacing))
    elif hasattr(block, "to_markdown"):
        try:
            flows.append(_paragraph(block.to_markdown(), template))
        except Exception:
            flows.append(_paragraph(str(block), template))
    return flows


def _render_section(section: Section, template: PDFTemplate) -> List[Any]:
    flowables: List[Any] = []
    flowables.append(_heading(section.title, section.level, template, section.pdf_style))
    flowables.append(Spacer(1, template.base_font_size * 0.35))
    for blk in section.blocks:
        flowables.extend(_block_flowables(blk, template))
        flowables.append(Spacer(1, template.base_font_size * 0.35))
    return flowables


def _default_footer(canvas_obj: canvas.Canvas, template: PDFTemplate, page_num: int) -> None:
    canvas_obj.saveState()
    canvas_obj.setFont(template.font, max(template.base_font_size - 1, 8))
    canvas_obj.setFillColor(colors.grey)
    width, _ = template.page_size
    canvas_obj.drawCentredString(width / 2, template.margin_bottom / 2, f"Page {page_num}")
    canvas_obj.restoreState()


def _on_page(template: PDFTemplate) -> Callable[[canvas.Canvas, Any], None]:
    def wrapper(canv: canvas.Canvas, doc: Any) -> None:
        page_num = canv.getPageNumber()
        if template.header_fn:
            template.header_fn(canv, template, page_num)
        if template.footer_fn:
            template.footer_fn(canv, template, page_num)
    return wrapper


def report_to_pdf(rpt: Report, out_pdf_path: str, template: Optional[PDFTemplate] = None) -> str:
    template = template or PDFTemplate()
    if template.footer_fn is None:
        template.footer_fn = _default_footer
    doc = template.make_document(out_pdf_path)
    story: List[Any] = []
    story.append(_heading(rpt.title, 1, template, rpt.pdf_style))
    if rpt.author:
        story.append(_paragraph(f"Author: {rpt.author}", template))
    if rpt.date_str:
        story.append(_paragraph(rpt.date_str, template))
    story.append(Spacer(1, template.base_font_size))
    for section in rpt.sections:
        story.extend(_render_section(section, template))
    on_page = _on_page(template)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return out_pdf_path


# ---- Minimal HTML/PDF helpers (public API) ----

def markdown_to_html(md_text: str, title: str = "Report", extra_css: Optional[str] = None) -> str:
    from markdown_it import MarkdownIt

    DEFAULT_CSS = (
        "@page { size: Letter; margin: 18mm 16mm 22mm 16mm; }\n"
        ":root { --text: #1f2328; --muted: #6a737d; }\n"
        "body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Noto Sans', sans-serif; color: var(--text); line-height: 1.5; }\n"
        "h1,h2,h3,h4 { page-break-after: avoid; }\n"
        "pre, code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }\n"
        "figure { margin: 0; text-align: center; }\n"
        "figcaption { color: var(--muted); font-size: 0.9em; margin-top: 4px; }\n"
        "table { width: 100%; border-collapse: collapse; }\n"
        "th, td { border: 1px solid #ccc; padding: 4px 8px; }\n"
    )
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough").enable("linkify")
    body = md.render(md_text)
    css = DEFAULT_CSS + ("\n" + extra_css if extra_css else "")
    return (
        f"<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<title>{title}</title>\n"
        f"<style>{css}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
    )


def markdown_to_pdf(
    md_text: str,
    out_pdf_path: str,
    base_url: str = ".",
    css_path: str | None = None,
    extra_css: str | None = None,
) -> str:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Image as RLImage

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    def make_heading(text: str) -> Paragraph:
        return Paragraph(f"<b>{text}</b>", normal)

    def try_table(start_idx: int, lines: List[str]) -> tuple[Optional[RLTable], int]:
        header_line = lines[start_idx]
        if start_idx + 1 >= len(lines):
            return None, 0
        sep_line = lines[start_idx + 1]
        if not header_line.strip().startswith("|") or not set(sep_line.strip()) <= set("|- "):
            return None, 0
        data: List[List[str]] = []
        header = [c.strip() for c in header_line.strip().strip("|").split("|")]
        data.append(header)
        i = start_idx + 2
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            data.append(row)
            i += 1
        tbl = RLTable(data)
        tbl.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
            ])
        )
        return tbl, (i - start_idx)

    anchor_line_re = re.compile(r"^\s*<a id=['\"][^'\"]+['\"]></a>\s*$")
    anchor_inline_re = re.compile(r"\s*<a id=['\"][^'\"]+['\"]></a>\s*$")

    def strip_anchor(text: str) -> str:
        return anchor_inline_re.sub("", text).strip()

    story: List[Any] = []
    raw_lines = md_text.splitlines()
    lines = [ln for ln in raw_lines if not anchor_line_re.match(ln)]
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            story.append(make_heading(strip_anchor(ln[2:]).strip()))
        elif ln.startswith("## "):
            story.append(make_heading(strip_anchor(ln[3:]).strip()))
        elif ln.startswith("### "):
            story.append(make_heading(strip_anchor(ln[4:]).strip()))
        elif ln.strip().startswith("|"):
            tbl, consumed = try_table(i, lines)
            if tbl is not None and consumed > 0:
                story.append(tbl)
                i += consumed
                continue
        elif ln.strip().startswith("![") and "](" in ln:
            try:
                start = ln.index("(")
                end = ln.index(")", start)
                path = ln[start + 1 : end]
                story.append(RLImage(path))
            except Exception:
                pass
        elif ln.strip():
            story.append(Paragraph(ln, normal))
        i += 1

    doc = SimpleDocTemplate(out_pdf_path, pagesize=letter)
    doc.build(story)
    return out_pdf_path
