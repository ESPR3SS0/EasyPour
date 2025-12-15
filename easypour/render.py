"""ReportLab PDF rendering utilities for EasyPour."""

from __future__ import annotations

import io
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepInFrame,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)
from reportlab.platypus import Image as RLImage
from reportlab.platypus import PageBreak as RLPageBreak
from reportlab.platypus import Table as RLTable

from .core import (
    DataFrameBlock,
    FigureBlock,
    InteractiveFigure,
    Report,
    Section,
    TableBlock,
)
from .core import (
    Image as CoreImage,
)
from .core import (
    PageBreak as CorePageBreak,
)
from .core import (
    Table as CoreTable,
)
from .inline import parse_inline
from .pdfmixins import (
    AbsoluteImageDirective,
    DoubleSpaceDirective,
    FloatingImageDirective,
    FlowableDirective,
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
class _NumberingState:
    figure: int = 0
    table: int = 0
    equation: int = 0


@dataclass
class PDFTemplate:
    """Customization settings for ReportLab PDF output."""

    page_size: Sequence[float] = letter
    margin_left: float = 54
    margin_right: float = 54
    margin_top: float = 64
    margin_bottom: float = 64
    layout: str = "single"
    first_page_layout: str | None = None
    column_gap: float = 18.0
    heading_overrides: dict[int, dict[str, Any]] = field(default_factory=dict)
    paragraph_overrides: dict[str, Any] = field(default_factory=dict)
    figure_caption_style: dict[str, Any] = field(default_factory=dict)
    table_caption_style: dict[str, Any] = field(default_factory=dict)
    figure_prefix: str = "Figure"
    table_prefix: str = "Table"
    section_spacing: float = 0.35
    custom_layouts: dict[str, Callable[[PDFTemplate], list[Frame]]] = field(default_factory=dict)
    autoscale_images: bool = True
    autoscale_tables: bool = True
    font_files: dict[str, str] = field(default_factory=dict)
    _registered_fonts: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _font_aliases: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    mono_font: str = "Courier"
    base_font_size: float = 10.5
    h1: float = 20
    h2: float = 16
    h3: float = 13
    line_spacing: float = 1.2

    text_color: Any = colors.black
    accent_color: Any = field(default_factory=lambda: colors.HexColor("#2b6cb0"))
    table_header_bg: Any = field(default_factory=lambda: colors.HexColor("#efefef"))
    table_header_text: Any = colors.black

    header_fn: Callable[[canvas.Canvas, PDFTemplate, int], None] | None = None
    footer_fn: Callable[[canvas.Canvas, PDFTemplate, int], None] | None = None

    def _page_size_tuple(self) -> tuple[float, float]:
        width, height = self.page_size
        return float(width), float(height)

    def register_layout(
        self,
        name: str,
        builder: Callable[[PDFTemplate], list[Frame]],
    ) -> PDFTemplate:
        """Register a custom layout builder by name."""
        self.custom_layouts[name.lower()] = builder
        return self

    def register_font_file(self, font_name: str, path: str | Path) -> PDFTemplate:
        """Associate a logical font name with a concrete font file path."""
        self.font_files[str(font_name)] = str(Path(path).expanduser())
        return self

    def _register_font_path(self, desired_name: str, font_path: Path) -> str:
        attempt = 0
        normalized_path = str(font_path.expanduser())
        while True:
            candidate = desired_name if attempt == 0 else f"{desired_name}_{attempt}"
            existing = self._registered_fonts.get(candidate)
            if existing == normalized_path:
                return candidate
            if existing is None:
                try:
                    pdfmetrics.getFont(candidate)
                except KeyError:
                    try:
                        pdfmetrics.registerFont(TTFont(candidate, normalized_path))
                    except Exception as exc:
                        raise RuntimeError(
                            f"Failed to register font '{candidate}' from {normalized_path}: {exc}"
                        ) from exc
                    self._registered_fonts[candidate] = normalized_path
                    return candidate
                attempt += 1
                continue
            attempt += 1

    def _resolve_font(self, font_value: str | None) -> str | None:
        if font_value is None:
            return None
        key = str(font_value)
        cached = self._font_aliases.get(key)
        if cached:
            return cached
        font_path: Path | None = None
        font_name = key
        if key in self.font_files:
            font_path = Path(self.font_files[key])
        else:
            candidate = Path(key).expanduser()
            if candidate.suffix.lower() in {".ttf", ".otf", ".ttc"} and candidate.is_file():
                font_path = candidate
                font_name = candidate.stem
        if font_path:
            resolved = self._register_font_path(font_name, font_path)
            self._font_aliases[key] = resolved
            return resolved
        return font_name

    def _normalize_font_style(self, style: dict[str, Any] | None) -> None:
        if not style:
            return
        for field_name in ("font", "font_name"):
            if style.get(field_name):
                style[field_name] = self._resolve_font(style[field_name])

    def _prepare_fonts(self) -> None:
        for attr in ("font", "font_bold", "mono_font"):
            resolved = self._resolve_font(getattr(self, attr, None))
            if resolved:
                setattr(self, attr, resolved)
        self._normalize_font_style(self.paragraph_overrides)
        for overrides in self.heading_overrides.values():
            self._normalize_font_style(overrides)
        self._normalize_font_style(self.figure_caption_style)
        self._normalize_font_style(self.table_caption_style)

    def _single_frames(self) -> list[Frame]:
        width, height = self._page_size_tuple()
        usable_width = width - self.margin_left - self.margin_right
        usable_height = height - self.margin_top - self.margin_bottom
        return [
            Frame(
                self.margin_left,
                self.margin_bottom,
                usable_width,
                usable_height,
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
            )
        ]

    def _two_column_frames(self) -> list[Frame]:
        width, height = self._page_size_tuple()
        usable_width = width - self.margin_left - self.margin_right
        usable_height = height - self.margin_top - self.margin_bottom
        col_width = max(48.0, (usable_width - self.column_gap) / 2.0)
        return [
            Frame(
                self.margin_left,
                self.margin_bottom,
                col_width,
                usable_height,
                leftPadding=0,
                rightPadding=self.column_gap / 2.0,
                topPadding=0,
                bottomPadding=0,
            ),
            Frame(
                self.margin_left + col_width + self.column_gap,
                self.margin_bottom,
                col_width,
                usable_height,
                leftPadding=self.column_gap / 2.0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
            ),
        ]

    def _frames_for_layout(self, layout_name: str) -> list[Frame] | None:
        name = layout_name.lower()
        if name == "single":
            return self._single_frames()
        if name == "two":
            return self._two_column_frames()
        builder = self.custom_layouts.get(name)
        if builder:
            return builder(self)
        return None

    def frame_bounds(self) -> tuple[float, float]:
        """Return conservative width/height bounds for the active layout."""
        layouts: list[str] = []
        layout_name = (self.layout or "single").lower()
        layouts.append(layout_name)
        if self.first_page_layout:
            layouts.append(self.first_page_layout.lower())
        widths: list[float] = []
        heights: list[float] = []
        for name in dict.fromkeys(layouts):
            frames = self._frames_for_layout(name)
            if frames:
                for frame in frames:
                    widths.append(float(getattr(frame, "_width", frame.width)))
                    heights.append(float(getattr(frame, "_height", frame.height)))
        if widths and heights:
            return min(widths), min(heights)
        width, height = self._page_size_tuple()
        return (
            width - self.margin_left - self.margin_right,
            height - self.margin_top - self.margin_bottom,
        )

    def make_document(
        self,
        output: str,
        on_page: Callable[[canvas.Canvas, Any], None] | None = None,
    ) -> BaseDocTemplate:
        """Create a BaseDocTemplate configured with this template's layout settings."""
        layout_name = (self.layout or "single").lower()
        main_frames = self._frames_for_layout(layout_name) or self._single_frames()
        first_frames: list[Frame] | None = None
        if self.first_page_layout:
            first_layout = self.first_page_layout.lower()
            first_frames = self._frames_for_layout(first_layout) or self._single_frames()

        doc = BaseDocTemplate(
            output,
            pagesize=self.page_size,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
        )

        def _cb(canv: canvas.Canvas, doc_obj: Any) -> None:
            if on_page:
                on_page(canv, doc_obj)

        templates: list[PageTemplate] = []
        if first_frames:
            templates.append(PageTemplate(id="First", frames=first_frames, onPage=_cb, pages=[1]))
        templates.append(PageTemplate(id="Main", frames=main_frames, onPage=_cb))
        doc.addPageTemplates(templates)
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
    overrides: dict[str, Any] | None = None,
    base_font: str | None = None,
    font_size: float | None = None,
) -> ParagraphStyle:
    merged: dict[str, Any] = dict(template.paragraph_overrides)
    if overrides:
        merged.update(overrides)
    font_name = (
        merged.get("font")
        or merged.get("font_name")
        or merged.get("fontName")
        or base_font
        or template.font
    )
    font_name = template._resolve_font(font_name) or template.font
    size = merged.get("font_size") or font_size or template.base_font_size
    leading = merged.get("leading") or (size * template.line_spacing)
    alignment_name = str(merged.get("alignment", "left")).lower()
    alignment = Alignment.get(alignment_name, TA_LEFT)
    color_value = (
        merged.get("color")
        or merged.get("text_color")
        or merged.get("textColor")
        or template.text_color
    )
    style = ParagraphStyle(
        name=f"style_{id(merged)}",
        fontName=font_name,
        fontSize=size,
        leading=leading,
        textColor=_color(color_value),
        alignment=alignment,
        spaceBefore=merged.get("space_before", 0),
        spaceAfter=merged.get("space_after", 0),
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
    pieces: list[str] = []
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


def _paragraph(
    text: str, template: PDFTemplate, overrides: dict[str, Any] | None = None
) -> Paragraph:
    style = _paragraph_style(template, overrides=overrides)
    html = _inline_to_html(text, template)
    return Paragraph(html, style)


def _heading(
    text: str, level: int, template: PDFTemplate, overrides: dict[str, Any] | None = None
) -> Paragraph:
    sizes = {1: template.h1, 2: template.h2, 3: template.h3}
    font_size = sizes.get(
        level, max(template.base_font_size, template.base_font_size + 2 - (level - 3))
    )
    merged = dict(template.heading_overrides.get(level, {}))
    if overrides:
        merged.update(overrides)
    style = _paragraph_style(
        template,
        overrides=merged,
        base_font=template.font_bold,
        font_size=font_size,
    )
    return Paragraph(_inline_to_html(text, template), style)


def _table(block: CoreTable, template: PDFTemplate) -> Flowable:
    data = [block.headers, *block.rows]
    style_opts = block.pdf_style or {}
    col_widths = style_opts.get("col_widths")
    row_heights = style_opts.get("row_heights")
    table = RLTable(data, colWidths=col_widths, rowHeights=row_heights, repeatRows=1)
    header_font = (
        template._resolve_font(style_opts.get("header_font") or template.font_bold)
        or template.font_bold
    )
    body_font = (
        template._resolve_font(style_opts.get("body_font") or template.font) or template.font
    )
    base_style = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            _color(style_opts.get("header_bg", template.table_header_bg)),
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            _color(style_opts.get("header_text", template.table_header_text)),
        ),
        ("FONTNAME", (0, 0), (-1, 0), header_font),
        ("FONTNAME", (0, 1), (-1, -1), body_font),
        ("FONTSIZE", (0, 0), (-1, -1), style_opts.get("font_size", template.base_font_size)),
        ("ALIGN", (0, 0), (-1, -1), style_opts.get("align", "LEFT")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            style_opts.get("grid_width", 0.25),
            _color(style_opts.get("grid_color", colors.grey)),
        ),
    ]
    if "style" in style_opts:
        base_style.extend(style_opts["style"])
    table.setStyle(TableStyle(base_style))
    if template.autoscale_tables:
        max_w, max_h = template.frame_bounds()
        scaled = _shrink_flowable(table, max_w, max_h)
        if scaled is not table:
            return scaled
    return table


_SHRINK_NEAR_UNIT = 0.999


def _shrink_flowable(
    flow: Flowable, max_width: float | None, max_height: float | None, *, min_scale: float = 0.4
) -> Flowable:
    usable_w = float(max_width) if max_width and max_width > 0 else None
    usable_h = float(max_height) if max_height and max_height > 0 else None
    if not usable_w and not usable_h:
        return flow
    fake = canvas.Canvas(io.BytesIO())
    width, height = flow.wrapOn(fake, usable_w or 10_000, usable_h or 10_000)
    need_width = usable_w is not None and width > usable_w + 0.5
    need_height = usable_h is not None and height > usable_h + 0.5
    if not (need_width or need_height):
        return flow
    width_scale = (usable_w / width) if need_width and width > 0 else 1.0
    height_scale = (usable_h / height) if need_height and height > 0 else 1.0
    scale = min(
        width_scale if width_scale > 0 else 1.0, height_scale if height_scale > 0 else 1.0, 1.0
    )
    if scale >= _SHRINK_NEAR_UNIT or scale < min_scale:
        return flow
    return _ScaledFlowable(flow, scale)


def _parse_dimension(value: Any, template: PDFTemplate, axis: str) -> float | None:
    """Convert user-provided dimensions to absolute point values."""
    result: float | None = None
    if value is None:
        return result
    if isinstance(value, int | float):
        result = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.endswith("px"):
            try:
                result = float(cleaned[:-2])
            except ValueError:
                result = None
        elif cleaned.endswith("%"):
            try:
                pct = float(cleaned[:-1]) / 100.0
            except ValueError:
                pct = None
            if pct is not None:
                max_w, max_h = template.frame_bounds()
                base = max_w if axis == "width" else max_h
                result = base * pct
    return result


def _image_size_from_hints(
    path: str,
    template: PDFTemplate,
    *,
    width_hint: Any = None,
    height_hint: Any = None,
    frame_bounds: tuple[float, float] | None = None,
) -> tuple[float, float]:
    reader = ImageReader(path)
    orig_w, orig_h = reader.getSize()
    orig_w = max(float(orig_w), 1.0)
    orig_h = max(float(orig_h), 1.0)
    width = _parse_dimension(width_hint, template, axis="width")
    height = _parse_dimension(height_hint, template, axis="height")
    if width is None and height is None:
        width = orig_w
        height = orig_h
    elif width is None and height is not None:
        height = float(height)
        width = orig_w * (height / orig_h if orig_h else 1.0)
    elif height is None and width is not None:
        width = float(width)
        height = orig_h * (width / orig_w if orig_w else 1.0)
    else:
        width = float(width)
        height = float(height)

    if width <= 0 and height <= 0:
        width = orig_w
        height = orig_h
    else:
        if width <= 0 and height > 0:
            width = orig_w * (height / orig_h if orig_h else 1.0)
        if height <= 0 and width > 0:
            height = orig_h * (width / orig_w if orig_w else 1.0)
    if width <= 0:
        width = orig_w
    if height <= 0:
        height = orig_h

    if template.autoscale_images and width > 0 and height > 0:
        max_w, max_h = frame_bounds if frame_bounds else template.frame_bounds()
        if not max_w or max_w <= 0:
            page_w, _ = template._page_size_tuple()
            max_w = max(page_w - template.margin_left - template.margin_right, 1.0)
        if not max_h or max_h <= 0:
            _, page_h = template._page_size_tuple()
            max_h = max(page_h - template.margin_top - template.margin_bottom, 1.0)
        scale = min(max_w / width if max_w else 1.0, max_h / height if max_h else 1.0, 1.0)
        if scale < 1.0:
            width *= scale
            height *= scale
    return width, height


def _image(block: CoreImage, template: PDFTemplate, *, include_caption: bool = True) -> list[Any]:
    flowables: list[Any] = []
    style = block.pdf_style or {}
    width_hint = style.get("width")
    if width_hint is None:
        width_hint = block.width
    height_hint = style.get("height")
    bounds = template.frame_bounds()
    width, height = _image_size_from_hints(
        block.path,
        template,
        width_hint=width_hint,
        height_hint=height_hint,
        frame_bounds=bounds,
    )
    max_w, max_h = bounds
    img = _ScalingImage(block.path, width=width, height=height, max_width=max_w, max_height=max_h)
    flowables.append(img)
    if include_caption and block.caption:
        flowables.append(Spacer(1, template.base_font_size * 0.2))
        cap_style = (
            style.get("caption_style")
            if style
            else {"font_size": template.base_font_size - 1, "color": colors.grey}
        )
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


class _ScalingImage(RLImage):
    def __init__(
        self,
        filename: str,
        *,
        max_width: float | None,
        max_height: float | None,
        **kwargs: Any,
    ):
        super().__init__(filename, **kwargs)
        self._max_width = max_width
        self._max_height = max_height

    def wrap(self, availWidth: float, availHeight: float):
        target_width = self._max_width
        if target_width is None or target_width <= 0:
            target_width = self.drawWidth
        if availWidth and availWidth > 0:
            target_width = min(target_width, availWidth) if target_width else availWidth
        target_height = self._max_height
        if target_height is None or target_height <= 0:
            target_height = self.drawHeight
        self._restrictSize(target_width, target_height)
        return super().wrap(availWidth, availHeight)


class _ScaledFlowable(Flowable):
    def __init__(self, inner: Flowable, scale: float):
        super().__init__()
        self.inner = inner
        self.scale = float(scale)
        self._wrapped: tuple[float, float] = (0.0, 0.0)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        scale = self.scale if self.scale > 0 else 1.0
        target_width = availWidth / scale if scale else availWidth
        target_height = availHeight / scale if scale else availHeight
        width, height = self.inner.wrap(target_width, target_height)
        self._wrapped = (width * scale, height * scale)
        return self._wrapped

    def draw(self) -> None:
        canv = self.canv
        canv.saveState()
        canv.scale(self.scale, self.scale)
        self.inner.drawOn(canv, 0, 0)
        canv.restoreState()


def _floating_image(block: FloatingImageDirective, template: PDFTemplate) -> list[Any]:
    bounds = template.frame_bounds()
    width, height = _image_size_from_hints(
        block.path,
        template,
        width_hint=block.width,
        height_hint=block.height,
        frame_bounds=bounds,
    )
    max_w, max_h = bounds
    img = _ScalingImage(block.path, width=width, height=height, max_width=max_w, max_height=max_h)
    align = block.align.lower()
    if align == "right":
        img.hAlign = "RIGHT"
    elif align == "center":
        img.hAlign = "CENTER"
    else:
        img.hAlign = "LEFT"
    flows: list[Any] = [img]
    if block.caption:
        flows.append(Spacer(1, block.padding))
        flows.append(
            _paragraph(
                block.caption,
                template,
                overrides={
                    "alignment": align if align in {"left", "right", "center"} else "left",
                    "color": colors.grey,
                },
            )
        )
    flows.append(Spacer(1, block.padding))
    return flows


def _figure_flowables(
    block: FigureBlock,
    template: PDFTemplate,
    numbering: _NumberingState,
    labels: dict[str, str],
) -> list[Any]:
    flows: list[Any] = []
    flows.extend(_image(block.image, template, include_caption=False))
    caption = block.caption or block.image.caption
    label_text: str | None = None
    if block.numbered:
        numbering.figure += 1
        label_text = f"{template.figure_prefix} {numbering.figure}"
        if block.label:
            labels[block.label] = label_text
    elif block.label:
        labels[block.label] = block.label
    if caption or label_text:
        text = " ".join(filter(None, [f"{label_text}." if label_text else None, caption]))
        flows.append(Spacer(1, template.base_font_size * 0.2))
        flows.append(
            _paragraph(
                text.strip(),
                template,
                overrides={
                    "alignment": "center",
                    "font": template.font,
                    "font_size": template.base_font_size - 1,
                    **template.figure_caption_style,
                },
            )
        )
    return flows


def _table_with_caption(
    block: TableBlock,
    template: PDFTemplate,
    numbering: _NumberingState,
    labels: dict[str, str],
) -> list[Any]:
    flows: list[Any] = [_table(block.table, template)]
    caption_parts: list[str] = []
    if block.numbered:
        numbering.table += 1
        label = f"{template.table_prefix} {numbering.table}"
        caption_parts.append(f"{label}.")
        if block.label:
            labels[block.label] = label
    elif block.label:
        labels[block.label] = block.label
    if block.caption:
        caption_parts.append(block.caption)
    if caption_parts:
        flows.append(Spacer(1, template.base_font_size * 0.2))
        flows.append(
            _paragraph(
                " ".join(caption_parts).strip(),
                template,
                overrides={
                    "alignment": "center",
                    "font": template.font_bold,
                    "font_size": template.base_font_size - 1,
                    **template.table_caption_style,
                },
            )
        )
    return flows


def _two_column_flowables(
    block: TwoColumnDirective,
    template: PDFTemplate,
    numbering: _NumberingState,
    labels: dict[str, str],
) -> list[Any]:
    left = []
    right = []
    for item in block.left:
        left.extend(_block_flowables(item, template, numbering, labels))
    for item in block.right:
        right.extend(_block_flowables(item, template, numbering, labels))
    usable = template.page_size[0] - template.margin_left - template.margin_right
    gap = block.gap
    col_width = max(10.0, (usable - gap) / 2)

    def _column(content: list[Any]) -> KeepInFrame:
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


def _render_dataframe(block: DataFrameBlock, template: PDFTemplate) -> list[Any]:
    try:
        import pandas as pd  # type: ignore

        df = block.data if hasattr(block.data, "columns") else pd.DataFrame(block.data)
        headers = list(df.columns)
        rows = df.values.tolist()
        tbl = _table(CoreTable(headers=headers, rows=rows), template)
        flows: list[Any] = [tbl]
        if block.caption:
            flows.append(Spacer(1, template.base_font_size * 0.2))
            flows.append(
                _paragraph(block.caption, template, {"alignment": "center", "color": colors.grey})
            )
        return flows
    except Exception:
        return [_paragraph(block.caption or "(DataFrame unavailable)", template)]


def _block_flowables(
    block: Any,
    template: PDFTemplate,
    numbering: _NumberingState,
    labels: dict[str, str],
) -> list[Any]:
    flows: list[Any] = []
    if isinstance(block, str):
        flows.append(_paragraph(block, template))
    elif isinstance(block, CoreTable):
        flows.append(_table(block, template))
    elif isinstance(block, CoreImage):
        flows.extend(_image(block, template))
    elif isinstance(block, FigureBlock):
        flows.extend(_figure_flowables(block, template, numbering, labels))
    elif isinstance(block, TableBlock):
        flows.extend(_table_with_caption(block, template, numbering, labels))
    elif isinstance(block, InteractiveFigure):
        flows.extend(_figure_flowables(block.figure, template, numbering, labels))
    elif isinstance(block, CorePageBreak):
        flows.append(RLPageBreak())
    elif isinstance(block, DataFrameBlock):
        flows.extend(_render_dataframe(block, template))
    elif isinstance(block, Section):
        flows.extend(_render_section(block, template, numbering, labels))
    elif isinstance(block, FlowableDirective):
        produced = block.factory(template)
        if produced is not None:
            if isinstance(produced, list | tuple):
                for item in produced:
                    if item is not None:
                        flows.append(item)
            else:
                flows.append(produced)
    elif isinstance(block, TwoColumnDirective):
        flows.extend(_two_column_flowables(block, template, numbering, labels))
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


def _render_section(
    section: Section,
    template: PDFTemplate,
    numbering: _NumberingState,
    labels: dict[str, str],
) -> list[Any]:
    flowables: list[Any] = []
    flowables.append(_heading(section.title, section.level, template, section.pdf_style))
    flowables.append(Spacer(1, template.base_font_size * template.section_spacing))
    for blk in section.blocks:
        flowables.extend(_block_flowables(blk, template, numbering, labels))
        flowables.append(Spacer(1, template.base_font_size * template.section_spacing))
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


def report_to_pdf(rpt: Report, out_pdf_path: str, template: PDFTemplate | None = None) -> str:
    """Render a Report instance to a PDF file and return the path."""
    template = template or PDFTemplate()
    template._prepare_fonts()
    if template.footer_fn is None:
        template.footer_fn = _default_footer
    numbering = _NumberingState()
    labels: dict[str, str] = {}
    on_page = _on_page(template)
    doc = template.make_document(out_pdf_path, on_page)
    story: list[Any] = []
    story.append(_heading(rpt.title, 1, template, rpt.pdf_style))
    if rpt.author:
        story.append(_paragraph(f"Author: {rpt.author}", template))
    if rpt.date_str:
        story.append(_paragraph(rpt.date_str, template))
    story.append(Spacer(1, template.base_font_size * template.section_spacing))
    for section in rpt.sections:
        story.extend(_render_section(section, template, numbering, labels))
    doc.build(story)
    return out_pdf_path


# ---- Minimal HTML/PDF helpers (public API) ----


def markdown_to_html(md_text: str, title: str = "Report", extra_css: str | None = None) -> str:
    """Convert Markdown text into a styled standalone HTML string."""
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
        f'<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>{title}</title>\n'
        f"<style>{css}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
    )


def markdown_to_pdf(
    md_text: str,
    output: str | Path,
    *,
    title: str = "Report",
    extra_css: str | None = None,
) -> str:
    """Render Markdown to PDF via WeasyPrint (HTML + CSS pipeline)."""
    html = markdown_to_html(md_text, title=title, extra_css=extra_css)
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency missing
        raise ImportError(
            "WeasyPrint is required for markdown_to_pdf(); install EasyPour[weasy] or pip install weasyprint."
        ) from exc
    out = Path(output)
    HTML(string=html).write_pdf(str(out))
    return str(out.resolve())
