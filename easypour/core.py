"""Core data structures and helpers for building EasyPour reports."""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
import unicodedata
import warnings
from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    Union,
    runtime_checkable,
)

from .pdfmixins import (
    AbsoluteImageDirective,
    DoubleSpaceDirective,
    FloatingImageDirective,
    FlowableDirective,
    TwoColumnDirective,
    VerticalSpaceDirective,
)

if TYPE_CHECKING:  # pragma: no cover - only for typing
    from .render import PDFTemplate

# =========================================================
# Inline helpers (portable Markdown-first)
# =========================================================


def bold(text: str) -> str:
    """Wrap text in Markdown bold markers."""
    return f"**{text}**"


def italic(text: str) -> str:
    """Wrap text in Markdown italics markers."""
    return f"*{text}*"


# Markdown has no native underline; use HTML <u> for terminal/Obsidian tolerance


def underline(text: str) -> str:
    """Wrap text in Markdown underline HTML."""
    return f"<u>{text}</u>"


def code(text: str) -> str:
    """Wrap text in Markdown code markers."""
    return f"`{text}`"


def url(text: str, url: str) -> str:
    """Create a Markdown link."""
    return f"[{text}]({url})"


def strikethrough(text: str) -> str:
    """Inline strikethrough using GitHub-Flavored Markdown syntax."""
    return f"~~{text}~~"


CODE_FENCE_MIN = 3


# =========================================================
# Protocols / Utilities
# =========================================================


@runtime_checkable
class MarkdownRenderable(Protocol):
    """Protocol for types that can produce Markdown strings."""

    def to_markdown(self) -> str:
        """Return a Markdown representation of the object."""


def _md_escape_cell(x: Any) -> str:
    """Escape Markdown table cell content (pipes/newlines)."""
    s = str(x)
    s = s.replace("|", r"\|")
    s = s.replace("\n", "<br>")
    return s


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "section"


# Simple asset manager for relocating images for HTML/PDF renders
@dataclass
class AssetManager:
    """Simple helper to relocate assets (images, figures) for renders."""

    base: Path = Path(".easypour_assets")

    def __post_init__(self) -> None:
        """Ensure the asset directory exists."""
        self.base.mkdir(parents=True, exist_ok=True)

    def put(self, src: Path | str, name: str | None = None) -> Path:
        """Copy an asset into the managed directory and return its path."""
        src_p = Path(src)
        dst = self.base / (name or src_p.name)
        try:
            if src_p.resolve() != dst.resolve():
                import shutil

                shutil.copy2(src_p, dst)
        except Exception:
            # Best-effort; ignore copy failures
            pass
        return dst


# =========================================================
# Blocks
# =========================================================


@dataclass
class Table:
    """Structured table data for reports."""

    headers: list[str]
    rows: list[list[str | int | float]]
    pdf_style: dict[str, Any] = field(default_factory=dict)  # placeholder for PDF-specific hints

    @classmethod
    def from_dicts(cls, rows: Iterable[dict[str, Any]]) -> Table:
        """Create a table from a sequence of dictionaries."""
        rows_l = list(rows)
        headers = list(rows_l[0].keys()) if rows_l else []
        body = [[row.get(h, "") for h in headers] for row in rows_l]
        return cls(headers, body)

    def to_markdown(self) -> str:
        """Serialize the table as GitHub-Flavored Markdown."""
        if not self.headers:
            return ""
        header = "| " + " | ".join(map(_md_escape_cell, self.headers)) + " |"
        sep = "| " + " | ".join("---" for _ in self.headers) + " |"
        body = "\n".join("| " + " | ".join(_md_escape_cell(c) for c in r) + " |" for r in self.rows)
        return f"{header}\n{sep}\n{body}\n"


@dataclass
class Image:
    """Image asset with optional alt/caption/width hints."""

    path: str
    alt: str = ""
    caption: str | None = None
    width: int | str | None = None
    pdf_style: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Render the image as Markdown/HTML."""
        md = f"![{self.alt}]({self.path})"
        if self.caption or self.width is not None:
            # Use HTML wrapper for width/caption while keeping MD-compatible core
            width_attr: str | None = None
            if isinstance(self.width, int):
                width_attr = f"{self.width}px"
            elif isinstance(self.width, str):
                width_attr = self.width
            style = f' style="width:{width_attr};"' if width_attr else ""
            cap = f"<figcaption>{self.caption}</figcaption>" if self.caption else ""
            return f"<figure{style}>{md}{cap}</figure>"
        return md


@dataclass
class PageBreak:
    """Explicit page break marker for rendered outputs."""

    def to_markdown(self) -> str:
        """Emit HTML compatible page-break element."""
        return "<div style='page-break-after: always;'></div>"


PAGE_BREAK = PageBreak()


@dataclass
class DataFrameBlock:
    """Wrapper for pandas-like data to render as a table."""

    data: Any
    caption: str | None = None

    def to_markdown(self) -> str:
        """Render the DataFrame as Markdown, falling back to text if unavailable."""
        try:
            import pandas as pd  # type: ignore

            df = self.data if hasattr(self.data, "to_markdown") else pd.DataFrame(self.data)
            md = df.to_markdown(index=False)
        except Exception:
            md = "> (DataFrame not renderable without pandas)"
        if self.caption:
            return f"{md}\n\n*{self.caption}*"
        return md


Block = Union[
    str,
    Table,
    Image,
    "InteractiveFigure",
    "FigureBlock",
    "TableBlock",
    "LayoutBlock",
    "Section",
    PageBreak,
    DataFrameBlock,
    FlowableDirective,
    TwoColumnDirective,
    AbsoluteImageDirective,
    FloatingImageDirective,
    VerticalSpaceDirective,
    DoubleSpaceDirective,
]


@dataclass
class FigureBlock:
    """Figure that combines an Image with caption/label info."""

    image: Image
    caption: str | None = None
    label: str | None = None
    numbered: bool = True


@dataclass
class TableBlock:
    """Table plus caption/label metadata."""

    table: Table
    caption: str | None = None
    label: str | None = None
    numbered: bool = False


@dataclass
class LayoutBlock:
    """Group of blocks that should share a specific layout template."""

    layout: str
    blocks: list[Block] = field(default_factory=list)
    keep_together: bool = True
    page_break_after: bool = True


@dataclass
class InteractiveFigure:
    """Wrapper for matplotlib/plotly hybrid figures."""

    figure: FigureBlock
    plotly_figure: dict[str, Any] | None = None


@dataclass
class Section:
    """Hierarchical building block containing text, tables, and figures."""

    title: str
    blocks: list[Block] = field(default_factory=list)
    level: int = 2  # 1..6; Report controls top-level
    pdf_style: dict[str, Any] = field(default_factory=dict)
    anchor: str | None = None

    # ----- block adders -----
    def add_text(self, *paragraphs: str) -> Section:
        """Append one or more paragraphs of text."""
        for p in paragraphs:
            self.blocks.append(p)
        return self

    def add_table(
        self,
        table: Table,
        *,
        caption: str | None = None,
        label: str | None = None,
        numbered: bool = False,
    ) -> Section:
        """Add a Table, optionally wrapping it with caption/label metadata."""
        if caption or label or numbered:
            self.blocks.append(
                TableBlock(table=table, caption=caption, label=label, numbered=numbered)
            )
        else:
            self.blocks.append(table)
        return self

    def add_image(
        self, image: Image, *, label: str | None = None, numbered: bool = False
    ) -> Section:
        """Insert an Image, promoting it to a FigureBlock when labeled/numbered."""
        if label or numbered:
            block = FigureBlock(image=image, caption=image.caption, label=label, numbered=numbered)
            self.blocks.append(block)
        else:
            self.blocks.append(image)
        return self

    def add_image_path(
        self,
        path: str | Path,
        *,
        alt: str = "",
        caption: str | None = None,
        width: int | str | None = None,
        label: str | None = None,
        numbered: bool = False,
    ) -> Section:
        """Add an image by filesystem path."""
        return self.add_image(
            Image(path=str(path), alt=alt, caption=caption, width=width),
            label=label,
            numbered=numbered,
        )

    def add_figure(
        self,
        path: str | Path,
        *,
        caption: str | None = None,
        label: str | None = None,
        width: int | str | None = None,
        alt: str = "",
    ) -> Section:
        """Add a figure with automatic numbering support."""
        img = Image(path=str(path), alt=alt, caption=caption, width=width)
        self.blocks.append(FigureBlock(image=img, caption=caption, label=label, numbered=True))
        return self

    def add_section(self, title: str) -> Section:
        """Add a nested subsection and return it for further editing."""
        child = Section(title=title, level=min(self.level + 1, 6))
        self.blocks.append(child)
        return child

    # ----- common markdown constructs -----
    def add_bullets(self, items: Iterable[str]) -> Section:
        """Add a simple unordered bullet list from an iterable of strings."""
        lst = "\n".join(f"- {x!s}" for x in items)
        if lst:
            self.blocks.append(lst)
        return self

    def add_checklist(self, items: Iterable[tuple[str, bool]]) -> Section:
        """Add a checklist where each item is (text, checked)."""
        lst = "\n".join(f"- [{'x' if done else ' '}] {text}" for (text, done) in items)
        if lst:
            self.blocks.append(lst)
        return self

    def add_codeblock(self, code_text: str, language: str | None = None) -> Section:
        """Add a fenced code block with optional language (robust against ``` inside)."""
        max_ticks = CODE_FENCE_MIN
        run = 0
        for ch in code_text:
            if ch == "`":
                run += 1
                max_ticks = max(run, max_ticks)
            else:
                run = 0
        fence = "`" * (max_ticks if max_ticks > CODE_FENCE_MIN else CODE_FENCE_MIN)
        if "```" in code_text and len(fence) == CODE_FENCE_MIN:
            fence = "````"
        lang = language or ""
        block = f"{fence}{lang}\n{code_text}\n{fence}"
        self.blocks.append(block)
        return self

    def add_strikethrough(self, text: str) -> Section:
        """Add a paragraph consisting of strikethrough text."""
        self.blocks.append(strikethrough(text))
        return self

    def add_math(
        self,
        formula: str,
        *,
        out_dir: str | Path = ".easypour_math",
        dpi: int = 220,
        caption: str | None = None,
        width: int | str | None = None,
        alt: str | None = None,
    ) -> Section:
        """Render a TeX-like formula to PNG (matplotlib mathtext) and insert as an image."""
        try:
            from .mathstub import (
                tex_to_png as _tex_to_png,  # local import to avoid hard matplotlib dep
            )
        except Exception as exc:  # pragma: no cover - import-time failure
            raise ImportError(
                "Matplotlib is required for add_math(); pip install matplotlib."
            ) from exc
        out_path = _tex_to_png(formula, Path(out_dir), dpi=dpi)
        return self.add_image(
            Image(
                path=str(out_path),
                alt=alt or formula,
                caption=caption,
                width=width,
            )
        )

    def add_matplotlib(
        self,
        obj: Any,
        *,
        out_dir: str | Path | None = None,
        filename: str | None = None,
        alt: str = "",
        caption: str | None = None,
        width: int | str | None = None,
        dpi: int = 180,
        interactive: bool = False,
        label: str | None = None,
        numbered: bool = True,
    ) -> Section:
        """Accept a matplotlib Figure or Axes, save as PNG, and add as an Image block.

        Parameters
        ----------
        - obj: matplotlib.figure.Figure or matplotlib.axes.Axes
        - out_dir: directory to save the PNG (defaults to .easypour_figs)
        - filename: optional PNG filename (defaults to mpl_{index}.png)
        - alt/caption/width: forwarded to Image()
        - dpi: DPI used when saving
        """
        fig = None
        if hasattr(obj, "savefig") and callable(getattr(obj, "savefig", None)):
            fig = obj
        elif hasattr(obj, "figure") and getattr(obj, "figure", None) is not None:
            fig = obj.figure
        else:
            raise TypeError("add_matplotlib expects a matplotlib Figure or Axes")

        base = Path(out_dir) if out_dir is not None else Path(".easypour_figs")
        base.mkdir(parents=True, exist_ok=True)
        fname = filename or f"mpl_{len(self.blocks)}.png"
        out_path = base / fname
        fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
        plotly_payload: dict[str, Any] | None = None
        if interactive:
            try:
                import plotly.io as pio  # type: ignore

                plotly_fig = pio.from_matplotlib(fig)
                plotly_payload = plotly_fig.to_dict()
            except Exception:
                plotly_payload = None
        # NEW: proactively close figure to avoid memory bloat in long sessions
        with suppress(Exception):
            import matplotlib.pyplot as _plt  # type: ignore

            _plt.close(fig)
        image = Image(path=str(out_path), alt=alt, caption=caption, width=width)
        if interactive:
            fig_block = FigureBlock(image=image, caption=caption, label=label, numbered=numbered)
            self.blocks.append(InteractiveFigure(figure=fig_block, plotly_figure=plotly_payload))
            return self
        if caption or label or numbered:
            self.blocks.append(
                FigureBlock(image=image, caption=caption, label=label, numbered=numbered)
            )
        else:
            self.blocks.append(image)
        return self

    # ----- PDF mixins / advanced layout -----
    def add_pdf_flowable(self, factory: Callable[[Any], Any]) -> Section:
        """Inject a custom ReportLab Flowable factory for full control."""
        self.blocks.append(FlowableDirective(factory=factory))
        return self

    def add_two_column_layout(
        self,
        left_blocks: Iterable[Block],
        right_blocks: Iterable[Block],
        *,
        gap: float = 12.0,
    ) -> Section:
        """Render two block lists side-by-side inside the PDF output."""
        self.blocks.append(
            TwoColumnDirective(left=list(left_blocks), right=list(right_blocks), gap=gap)
        )
        return self

    def add_absolute_image(
        self,
        path: str | Path,
        *,
        x: float,
        y: float,
        width: float | None = None,
        height: float | None = None,
        page: int | None = None,
    ) -> Section:
        """Position an image using absolute ReportLab coordinates (points)."""
        self.blocks.append(
            AbsoluteImageDirective(
                path=str(path),
                x=float(x),
                y=float(y),
                width=width,
                height=height,
                page=page,
            )
        )
        return self

    def add_floating_image(
        self,
        path: str | Path,
        *,
        align: str = "left",
        width: float | None = None,
        height: float | None = None,
        caption: str | None = None,
        padding: float = 6.0,
    ) -> Section:
        """Add an image that floats left/right/center with optional caption."""
        self.blocks.append(
            FloatingImageDirective(
                path=str(path),
                align=align,
                width=width,
                height=height,
                caption=caption,
                padding=padding,
            )
        )
        return self

    def add_vertical_space(self, height: float) -> Section:
        """Insert raw vertical whitespace (points) into the PDF output."""
        self.blocks.append(VerticalSpaceDirective(height=float(height)))
        return self

    def add_double_space(self) -> Section:
        """Insert a spacer roughly equivalent to an extra blank line."""
        self.blocks.append(DoubleSpaceDirective())
        return self

    def add_new_page(self) -> Section:
        """Insert a hard page break in every renderer that supports it."""
        self.blocks.append(PAGE_BREAK)
        return self

    def add_layout_block(
        self,
        layout: str,
        *blocks: Block,
        keep_together: bool = True,
        page_break_after: bool = True,
    ) -> Section:
        """Add a group of blocks that should share a specific page layout."""
        payload = list(blocks)
        self.blocks.append(
            LayoutBlock(
                layout=layout,
                blocks=payload,
                keep_together=keep_together,
                page_break_after=page_break_after,
            )
        )
        return self

    # ----- render to markdown -----
    def to_markdown(self) -> str:
        """Render this section (and nested sections) to Markdown."""
        self.anchor = self.anchor or _slug(self.title)
        lines: list[str] = [f"{'#' * self.level} {self.title}"]
        lines.append(f"<a id='{self.anchor}'></a>")
        lines.append("")
        for blk in self.blocks:
            # Custom per-type rendering
            if isinstance(blk, str):
                lines += [blk, ""]
            elif isinstance(blk, Table | Image):
                lines += [blk.to_markdown(), ""]
            elif isinstance(blk, InteractiveFigure):
                lines += [blk.figure.image.to_markdown(), ""]
                caption = blk.figure.caption or blk.figure.image.caption
                label_text = getattr(blk.figure, "_mf_label_text", "Figure")
                if caption:
                    lines += [f"**{label_text}:** {caption}", ""]
            elif isinstance(blk, FigureBlock):
                lines += [blk.image.to_markdown(), ""]
                label_text = getattr(blk, "_mf_label_text", "Figure")
                caption = blk.caption or blk.image.caption
                if caption:
                    lines += [f"**{label_text}:** {caption}", ""]
            elif isinstance(blk, PageBreak | DataFrameBlock):
                lines += [blk.to_markdown(), ""]
            elif isinstance(blk, TableBlock):
                lines += [blk.table.to_markdown(), ""]
                label_text = getattr(blk, "_mf_label_text", "Table")
                if blk.caption:
                    lines += [f"*{label_text}:* {blk.caption}", ""]
            elif isinstance(blk, Section):
                # ensure nested section levels don't exceed h6
                blk.level = min(self.level + 1, 6)
                lines += [blk.to_markdown(), ""]
            elif isinstance(blk, MarkdownRenderable) or hasattr(blk, "to_markdown"):
                # Protocol/fallback: any custom block with to_markdown()
                with suppress(Exception):
                    lines += [blk.to_markdown(), ""]  # type: ignore[attr-defined]
        return "\n".join(lines).strip()


# =========================================================
# Report
# =========================================================


@dataclass
class Report:
    """Top-level container holding sections plus render configuration."""

    title: str
    author: str | None = None
    date_str: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    sections: list[Section] = field(default_factory=list)
    pdf_style: dict[str, Any] = field(default_factory=dict)
    pdf_template_options: dict[str, Any] = field(default_factory=dict)

    # Streamlit customization/state
    streamlit_options: dict[str, Any] = field(default_factory=dict)
    streamlit_hooks: dict[str, Callable[..., Any]] = field(default_factory=dict)
    streamlit_renderers: dict[type, Callable[[Any, Any, Report], None]] = field(
        default_factory=dict
    )
    streamlit_theme: dict[str, str] = field(default_factory=dict)

    # Dash options
    dash_options: dict[str, Any] = field(default_factory=dict)
    dash_css_text: str | None = field(default=None)
    references: dict[str, str] = field(default_factory=dict)

    _st: Any | None = field(default=None, repr=False, compare=False)
    _citation_index: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _citation_order: list[str] = field(default_factory=list, init=False, repr=False)
    _label_index: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    # ---------- PDF ----------
    def write_pdf(self, path: str, template: PDFTemplate | None = None) -> str:  # type: ignore[name-defined]
        """Render this report to a PDF using the provided (or default) template."""
        self._ensure_label_index()
        from .render import PDFTemplate, report_to_pdf  # local import to avoid circular dependency

        supplied_template = template is not None
        tpl = template or PDFTemplate()
        self._apply_pdf_template_overrides(tpl, user_template=supplied_template)
        return report_to_pdf(self, out_pdf_path=path, template=tpl)

    def configure_pdf(self, **options) -> Report:
        """Configure PDF-level layout defaults without manually creating a template.

        Supported keys include:
        - page_size: tuple/list of (width, height) in points
        - margins: iterable of four values (left, right, top, bottom) in points
        - margin_left/margin_right/margin_top/margin_bottom: individual overrides
        - layout / first_page_layout / column_gap
        - font, font_bold, mono_font, base_font_size, h1, h2, h3, line_spacing
        - header_fn / footer_fn: callables with signature (canvas, template, page_num)
        - figure_caption_style / table_caption_style: dicts merged into caption styles
        - heading_overrides: dict mapping heading level -> ParagraphStyle overrides
        - paragraph_overrides: dict merged into template paragraph defaults
        - page_layouts: sequence describing layout names per page (strings or (layout, count) tuples)
        - autoscale_images / autoscale_tables: toggle automatic sizing safeguards
        """
        for key, value in options.items():
            if key in {"figure_caption_style", "table_caption_style"} and isinstance(value, dict):
                merged = dict(self.pdf_template_options.get(key, {}))
                merged.update(value)
                self.pdf_template_options[key] = merged
            elif key == "font_files" and isinstance(value, dict):
                merged = dict(self.pdf_template_options.get(key, {}))
                merged.update({str(k): str(v) for k, v in value.items()})
                self.pdf_template_options[key] = merged
            elif key == "margins":
                self.pdf_template_options[key] = tuple(value)  # type: ignore[arg-type]
            else:
                self.pdf_template_options[key] = value
        return self

    def add_section(self, title: str) -> Section:
        """Create a new top-level section and return it."""
        sec = Section(title=title, level=2)
        self.sections.append(sec)
        return sec

    def add_page_break(self) -> Report:
        """Insert a top-level page break between sections."""
        self.sections.append(Section(title="", blocks=[PAGE_BREAK], level=2))
        return self

    # ---------- utils ----------
    def walk(self) -> Iterable[Section]:
        """Yield every section/subsection in depth-first order."""

        def _rec(s: Section):
            yield s
            for b in s.blocks:
                if isinstance(b, Section):
                    yield from _rec(b)

        for s in self.sections:
            yield from _rec(s)

    def _apply_pdf_template_overrides(self, template: PDFTemplate, *, user_template: bool) -> None:  # type: ignore[name-defined]
        """Apply configure_pdf overrides to the given template instance."""
        if not self.pdf_template_options:
            return

        def warn_override(attr: str, old: Any, new: Any) -> None:
            warnings.warn(
                f"configure_pdf() overriding template.{attr} (was {old!r}, now {new!r})",
                UserWarning,
                stacklevel=3,
            )

        def assign(attr: str, value: Any) -> None:
            current = getattr(template, attr)
            if user_template and current != value:
                warn_override(attr, current, value)
            setattr(template, attr, value)

        overrides = self.pdf_template_options
        if "margins" in overrides:
            margins = overrides["margins"]
            _MARGIN_COUNT = 4
            if not isinstance(margins, (list | tuple)) or len(margins) != _MARGIN_COUNT:
                raise ValueError(
                    "configure_pdf(margins=...) expects four values (left, right, top, bottom)."
                )
            left, right, top, bottom = margins
            assign("margin_left", float(left))
            assign("margin_right", float(right))
            assign("margin_top", float(top))
            assign("margin_bottom", float(bottom))

        direct_attrs = {
            "page_size",
            "margin_left",
            "margin_right",
            "margin_top",
            "margin_bottom",
            "layout",
            "first_page_layout",
            "column_gap",
            "font",
            "font_bold",
            "mono_font",
            "base_font_size",
            "h1",
            "h2",
            "h3",
            "line_spacing",
            "header_fn",
            "footer_fn",
            "autoscale_images",
            "autoscale_tables",
        }
        for attr in direct_attrs:
            if attr in overrides:
                assign(attr, overrides[attr])

        if "font_files" in overrides:
            for name, path in dict(overrides["font_files"]).items():
                normalized = str(Path(path))
                current = template.font_files.get(name)
                if user_template and current and current != normalized:
                    warn_override(f"font_files[{name!r}]", current, normalized)
                template.font_files[name] = normalized

        if "page_layouts" in overrides:
            template.page_layouts = list(overrides["page_layouts"])

        for style_key in ("figure_caption_style", "table_caption_style"):
            if style_key in overrides:
                style_update = dict(overrides[style_key])
                base = getattr(template, style_key)
                for key, value in style_update.items():
                    old = base.get(key)
                    if user_template and old != value:
                        warn_override(f"{style_key}.{key}", old, value)
                base.update(style_update)

        if "paragraph_overrides" in overrides:
            paragraph_update = dict(overrides["paragraph_overrides"])
            for key, value in paragraph_update.items():
                old = template.paragraph_overrides.get(key)
                if user_template and old != value:
                    warn_override(f"paragraph_overrides.{key}", old, value)
            template.paragraph_overrides.update(paragraph_update)

        if "heading_overrides" in overrides:
            heading_updates = overrides["heading_overrides"]
            for level_str, update in heading_updates.items():
                try:
                    level = int(level_str)
                except Exception:
                    raise ValueError("heading_overrides keys must be integers.") from None
                target = template.heading_overrides.setdefault(level, {})
                for key, value in update.items():
                    old = target.get(key)
                    if user_template and old != value:
                        warn_override(f"heading_overrides[{level}].{key}", old, value)
                    target[key] = value

    def find_section(self, title: str) -> Section | None:
        """Locate a section by case-insensitive title."""
        t = title.strip().lower()
        for s in self.walk():
            if s.title.strip().lower() == t:
                return s
        return None

    # ---------- render paths ----------
    def _build_toc(self) -> list[str]:
        """Generate a Markdown-formatted table-of-contents."""
        toc = ["## Table of Contents", ""]

        def _iter(sec: Section) -> Iterable[Section]:
            yield sec
            for blk in sec.blocks:
                if isinstance(blk, Section):
                    yield from _iter(blk)

        for s in self.sections:
            for sec in _iter(s):
                indent = "  " * max(0, sec.level - 2)
                anchor = sec.anchor or _slug(sec.title)
                toc.append(f"{indent}- [{sec.title}](#{anchor})")
        return toc

    def to_markdown(self, *, asset_base: Path | None = None) -> str:
        """Serialize the full report to Markdown."""
        self._ensure_label_index()
        dt = self.date_str or date.today().isoformat()
        front_matter = [
            "---",
            f'title: "{self.title}"',
            f'author: "{self.author}"' if self.author else None,
            f"date: {dt}",
            *(f"{k}: {v}" for k, v in self.meta.items()),
            "---",
            "",
        ]
        front = "\n".join([x for x in front_matter if x is not None])

        # Optionally relocate assets into a dedicated folder and rewrite paths temporarily
        img_restore: list[tuple[Image, str]] = []
        if asset_base is not None:
            am = AssetManager(base=Path(asset_base))
            for sec in self.walk():
                for _, blk in enumerate(list(sec.blocks)):
                    if isinstance(blk, Image):
                        try:
                            newp = am.put(blk.path)
                            img_restore.append((blk, blk.path))
                            blk.path = str(Path(asset_base) / newp.name)
                        except Exception:
                            pass

        parts = [front, f"# {self.title}", ""]
        if self.author:
            parts += [f"**Author:** {self.author}", ""]
        parts += [f"*{dt}*", ""]

        # TOC
        toc = self._build_toc()
        _TOC_MIN_ENTRIES = 2
        if len(toc) > _TOC_MIN_ENTRIES:
            parts += ["\n".join(toc), ""]

        for s in self.sections:
            parts += [s.to_markdown(), ""]
        md = "\n".join(parts).strip()

        # Restore original image paths
        for blk, old in img_restore:
            blk.path = old

        return md

    def write_markdown(self, path: str | Path) -> str:
        """Write `to_markdown()` output to disk and return the path."""
        self._ensure_label_index()
        md = self.to_markdown()
        p = Path(path)
        with open(p, "w", encoding="utf-8") as f:
            f.write(md + "\n")
        return str(p.resolve())

    def __repr__(self) -> str:
        """Return a concise representation including section headings.

        Example:
            Report(title='Demo', headings=['Summary', 'Metrics', 'Notes > Todo'])
        """
        paths: list[str] = []

        def walk(sec: Section, parent: list[str]) -> None:
            full = [*parent, sec.title]
            paths.append(" > ".join(full))
            for blk in sec.blocks:
                if isinstance(blk, Section):
                    walk(blk, full)

        for s in self.sections:
            walk(s, [])

        hs = ", ".join(repr(p) for p in paths)
        return f"Report(title={self.title!r}, headings=[{hs}])"

    # ---------- streamlit customization API ----------
    def configure_streamlit(self, **options) -> Report:
        """Configure default Streamlit options.

        Supported keys:
        - page_title: str
        - layout: "centered" | "wide"
        - height: int (HTML preview height)
        - tabs: list[str] (any of ["Report", "Markdown", "HTML", "PDF"], order respected)
        """
        self.streamlit_options.update(options)
        return self

    def set_streamlit_hooks(
        self,
        *,
        sidebar: Callable[[Any, Report], None] | None = None,
        before_render: Callable[[Any, Report], None] | None = None,
        after_render: Callable[[Any, Report], None] | None = None,
    ) -> Report:
        """Register callback hooks for Streamlit rendering.

        - sidebar(st, report): called inside st.sidebar before rendering content
        - before_render(st, report): called after title/caption, before tabs
        - after_render(st, report): called after tabs are rendered
        """
        if sidebar is not None:
            self.streamlit_hooks["sidebar"] = sidebar
        if before_render is not None:
            self.streamlit_hooks["before_render"] = before_render
        if after_render is not None:
            self.streamlit_hooks["after_render"] = after_render
        return self

    def register_streamlit_renderer(
        self, block_type: type, renderer: Callable[[Any, Any, Report], None]
    ) -> Report:
        """Associate a custom renderer for a specific block type.

        The renderer signature is (st, block, report) and should emit Streamlit widgets.
        """
        self.streamlit_renderers[block_type] = renderer
        return self

    def set_streamlit_theme(
        self,
        *,
        primary_color: str | None = None,
        background_color: str | None = None,
        text_color: str | None = None,
        secondary_background_color: str | None = None,
        link_color: str | None = None,
        font_family: str | None = None,
        css: str | None = None,
    ) -> Report:
        """Set simple theming via injected CSS in Streamlit.

        Colors should be CSS color values (e.g., "#ff6600" or "rgb(10,10,10)").
        If `css` is provided, it is injected verbatim in a <style> tag after computed rules.
        """
        theme: dict[str, str] = {}
        if primary_color:
            theme["primary_color"] = primary_color
        if background_color:
            theme["background_color"] = background_color
        if text_color:
            theme["text_color"] = text_color
        if secondary_background_color:
            theme["secondary_background_color"] = secondary_background_color
        if link_color:
            theme["link_color"] = link_color
        if font_family:
            theme["font_family"] = font_family
        if css:
            theme["css"] = css
        self.streamlit_theme.update(theme)
        return self

    def configure_dash(
        self,
        *,
        external_stylesheets: list[str] | None = None,
        css_text: str | None = None,
        tabs: list[str] | None = None,
        preview_height: str | None = None,
        page_title: str | None = None,
    ) -> Report:
        """Configure Dash theming and layout options.

        - external_stylesheets: list of CSS URLs (e.g., Bootstrap)
        - css_text: raw CSS string injected via ``<style>`` in the layout
        - tabs: ordered list of tabs to show (subset of ["Report", "Markdown", "HTML", "PDF"])
        - preview_height: height used for Markdown/HTML preview panes (e.g., "70vh")
        - page_title: browser tab title override
        """
        if external_stylesheets is not None:
            self.dash_options["external_stylesheets"] = list(external_stylesheets)
        if css_text is not None:
            self.dash_css_text = css_text
        if tabs is not None:
            self.dash_options["tabs"] = list(tabs)
        if preview_height is not None:
            self.dash_options["preview_height"] = preview_height
        if page_title is not None:
            self.dash_options["page_title"] = page_title
        return self

    # ---------- references / citations ----------
    def add_reference(self, key: str, entry: str) -> Report:
        """Register a reference entry (e.g., bibliography string)."""
        self.references[key] = entry
        return self

    def cite(self, key: str) -> str:
        """Return an IEEE-style numeric citation like [1], tracking order of first use."""
        if key not in self.references:
            raise KeyError(f"Reference '{key}' is not registered.")
        if key not in self._citation_index:
            self._citation_order.append(key)
            self._citation_index[key] = len(self._citation_order)
        return f"[{self._citation_index[key]}]"

    def ensure_references_section(self, title: str = "References") -> Section:
        """Populate (or create) a references section ordered by citation usage."""
        self._ensure_label_index()
        sec = self.find_section(title) or self.add_section(title)
        sec.blocks = []
        for idx, key in enumerate(self._citation_order, start=1):
            entry = self.references.get(key)
            if entry:
                sec.add_text(f"[{idx}] {entry}")
        return sec

    # ---------- figure/table labels ----------
    def _ensure_label_index(self) -> dict[str, str]:
        fig_prefix = self.meta.get("figure_prefix", "Figure")
        table_prefix = self.meta.get("table_prefix", "Table")
        figure_counter = 0
        table_counter = 0
        label_index: dict[str, str] = {}

        def assign_figure(block: FigureBlock) -> None:
            nonlocal figure_counter
            needs_number = block.numbered or bool(block.label)
            if needs_number:
                figure_counter += 1
                label_text = f"{fig_prefix} {figure_counter}"
            else:
                label_text = fig_prefix
            block._mf_label_text = label_text
            if block.label:
                label_index[block.label] = label_text

        def assign_table(block: TableBlock) -> None:
            nonlocal table_counter
            needs_number = block.numbered or bool(block.label)
            if needs_number:
                table_counter += 1
                label_text = f"{table_prefix} {table_counter}"
            else:
                label_text = table_prefix
            block._mf_label_text = label_text
            if block.label:
                label_index[block.label] = label_text

        def walk(sec: Section) -> None:
            for blk in sec.blocks:
                if isinstance(blk, InteractiveFigure):
                    assign_figure(blk.figure)
                elif isinstance(blk, FigureBlock):
                    assign_figure(blk)
                elif isinstance(blk, TableBlock):
                    assign_table(blk)
                elif isinstance(blk, Section):
                    walk(blk)

        for section in self.sections:
            walk(section)

        self._label_index = label_index
        return label_index

    def ref(self, label: str, *, default: str | None = None) -> str:
        """Return the numbered label (e.g., ``Figure 2``) for a reference."""
        index = self._ensure_label_index()
        if label in index:
            return index[label]
        if default is not None:
            return default
        raise KeyError(f"Label '{label}' not found in this report.")

    @property
    def st(self):  # pragma: no cover - depends on streamlit runtime
        """Return the Streamlit module instance used by show_streamlit()."""
        if self._st is not None:
            return self._st
        try:
            import streamlit as st  # type: ignore

            self._st = st
            return st
        except Exception as e:
            raise RuntimeError("Streamlit is not available in this context.") from e

    # ---------- interactive previews ----------
    def show_streamlit(self, *, height: int = 420) -> None:
        """Render this report inside a Streamlit app with helpful tabs."""
        self._ensure_label_index()
        try:
            import streamlit as st  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency
            raise ImportError("Streamlit is required: pip install streamlit") from e

        # Make the Streamlit instance accessible after this call
        self._st = st

        # Build artifacts once
        md = self.to_markdown()
        try:
            from .render import markdown_to_html
        except Exception as e:  # pragma: no cover
            raise RuntimeError("Render helpers unavailable.") from e

        # Options (with reasonable defaults)
        page_title = self.streamlit_options.get("page_title", f"EasyPour — {self.title}")
        layout = self.streamlit_options.get("layout", "wide")
        tabs = self.streamlit_options.get("tabs", ["Report", "Markdown", "HTML", "PDF"])
        height = int(self.streamlit_options.get("height", height))

        # Best effort page config (ignore if too late in script execution)
        with suppress(Exception):
            st.set_page_config(page_title=page_title, layout=layout)

        # Apply simple theme via CSS injection if provided
        if self.streamlit_theme:
            rules: list[str] = []
            bg = self.streamlit_theme.get("background_color")
            text = self.streamlit_theme.get("text_color")
            link = self.streamlit_theme.get("link_color")
            font = self.streamlit_theme.get("font_family")
            secondary_bg = self.streamlit_theme.get("secondary_background_color")
            primary = self.streamlit_theme.get("primary_color")
            if bg or text or font:
                rules.append(
                    "body {"
                    + (f" background-color: {bg};" if bg else "")
                    + (f" color: {text};" if text else "")
                    + (f" font-family: {font};" if font else "")
                    + " }"
                )
            if link:
                rules.append(f"a, a:visited {{ color: {link}; }}")
            # Streamlit containers (best-effort selectors)
            if secondary_bg:
                rules.append(
                    "[data-testid='stSidebar'], .sidebar .sidebar-content {"
                    + f" background-color: {secondary_bg};"
                    + " }"
                )
            if primary:
                # Buttons and slider accents (best-effort)
                rules.append(
                    ".stButton>button, .stDownloadButton>button {"
                    + f" background-color: {primary}; border-color: {primary};"
                    + " }"
                )
            extra_css = self.streamlit_theme.get("css")
            css_block = "\n".join(rules + ([extra_css] if extra_css else []))
            if css_block.strip():
                st.markdown(f"<style>{css_block}</style>", unsafe_allow_html=True)

        st.title(self.title)
        if self.author:
            st.caption(f"Author: {self.author}")

        # Sidebar hook (if any)
        if (hook := self.streamlit_hooks.get("sidebar")) is not None:
            try:
                with st.sidebar:
                    hook(st, self)
            except Exception:
                st.warning("Sidebar hook failed.")

        # Hook before rendering content
        if (hook := self.streamlit_hooks.get("before_render")) is not None:
            try:
                hook(st, self)
            except Exception:
                st.warning("before_render hook failed.")

        # Tabs (configurable subset/order)
        tabs_created = st.tabs(tabs)  # type: ignore[assignment]
        tab_lookup = {name: tabs_created[i] for i, name in enumerate(tabs)}

        def _stable_key(*parts: str) -> str:
            h = hashlib.md5("||".join(parts).encode()).hexdigest()[:10]
            return f"k_{h}"

        def _display_image_block(img: Image):
            use_container = None
            w_px: int | None = None
            if img.width is not None:
                if isinstance(img.width, str):
                    w = img.width.strip()
                    if w.endswith("%"):
                        use_container = True
                    elif w.endswith("px"):
                        try:
                            w_px = int(w[:-2])
                        except Exception:
                            w_px = None
                elif isinstance(img.width, int):
                    w_px = img.width
            try:
                st.image(
                    img.path,
                    caption=img.caption,
                    width=w_px,
                    use_container_width=use_container,
                )  # type: ignore[call-arg]
            except TypeError:
                st.image(img.path, caption=img.caption, width=w_px, use_column_width=use_container)

        def _render_section(sec: Section):
            # Map heading level to Streamlit headers
            _H1_H2_MAX = 2
            _H3_LEVEL = 3
            if sec.level <= _H1_H2_MAX:
                st.header(sec.title)
            elif sec.level == _H3_LEVEL:
                st.subheader(sec.title)
            else:
                st.markdown(f"{'#' * sec.level} {sec.title}")

            for blk in sec.blocks:
                # Custom renderer mapping by exact type
                r_fn = self.streamlit_renderers.get(type(blk))
                if r_fn is not None:
                    try:
                        r_fn(st, blk, self)
                        continue
                    except Exception as e:
                        st.warning(f"Custom renderer failed for {type(blk).__name__}: {e}")

                if isinstance(blk, str):
                    st.markdown(blk, unsafe_allow_html=True)
                elif isinstance(blk, Image):
                    _display_image_block(blk)
                elif isinstance(blk, Table):
                    try:
                        import pandas as pd  # type: ignore

                        df = pd.DataFrame(blk.rows, columns=blk.headers)
                        st.table(df)
                    except Exception:
                        st.table([dict(zip(blk.headers, r, strict=False)) for r in blk.rows])
                elif isinstance(blk, InteractiveFigure):
                    displayed = False
                    if blk.plotly_figure:
                        try:
                            import plotly.graph_objects as go  # type: ignore

                            st.plotly_chart(go.Figure(blk.plotly_figure), use_container_width=True)
                            displayed = True
                        except Exception:
                            displayed = False
                    if not displayed:
                        _display_image_block(blk.figure.image)
                    if blk.figure.caption:
                        st.caption(blk.figure.caption)
                elif isinstance(blk, DataFrameBlock):
                    try:
                        import pandas as pd  # type: ignore

                        st.dataframe(pd.DataFrame(blk.data))
                        if blk.caption:
                            st.caption(blk.caption)
                    except Exception:
                        st.text("(DataFrame unavailable)")
                elif isinstance(blk, PageBreak):
                    # No-op in Streamlit; keep layout simple
                    st.divider()
                elif isinstance(blk, Section):
                    _render_section(blk)
                elif isinstance(blk, MarkdownRenderable) or hasattr(blk, "to_markdown"):
                    try:
                        st.markdown(blk.to_markdown(), unsafe_allow_html=True)  # type: ignore[attr-defined]
                    except Exception:
                        st.warning(f"Could not render custom block: {type(blk).__name__}")

        if "Report" in tab_lookup:
            with tab_lookup["Report"]:
                for s in self.sections:
                    _render_section(s)

        if "Markdown" in tab_lookup:
            with tab_lookup["Markdown"]:
                st.code(md, language="markdown")

        if "HTML" in tab_lookup:
            with tab_lookup["HTML"]:
                html_doc = markdown_to_html(md, title=self.title)
                # Convert relative img src to file URIs so iframe can load them
                try:
                    from pathlib import Path as _P

                    def _repl(m):
                        p = m.group(1)
                        if p.startswith("http://") or p.startswith("https://"):
                            return m.group(0)
                        q = _P(p)
                        if not q.is_absolute():
                            q = _P(".").joinpath(q)
                        if q.exists():
                            return f'src="{q.resolve().as_uri()}"'
                        return m.group(0)

                    html_doc = re.sub(r'src="([^"]+)"', _repl, html_doc)
                except Exception:
                    pass
                st.components.v1.html(html_doc, height=height, scrolling=True)

        if "PDF" in tab_lookup:
            with tab_lookup["PDF"]:
                # Generate a PDF on demand; degrade gracefully if ReportLab missing
                import tempfile

                try:
                    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                        self.write_pdf(tmp.name)
                        data = Path(tmp.name).read_bytes()
                    st.download_button(
                        "Download PDF",
                        data=data,
                        file_name="report.pdf",
                        mime="application/pdf",
                    )
                except Exception:
                    st.info("PDF generation is unavailable. Install ReportLab to enable.")

        # Hook after rendering content
        if (hook := self.streamlit_hooks.get("after_render")) is not None:
            try:
                hook(st, self)
            except Exception:
                st.warning("after_render hook failed.")

    def to_dash_app(self):  # pragma: no cover - optional dependency helper
        """Return a Dash app mirroring this report with interactive widgets."""
        self._ensure_label_index()

        try:
            from dash import Dash, Input, Output, dcc, html  # type: ignore

            try:
                from dash import dash_table  # type: ignore
            except Exception:
                dash_table = None  # type: ignore
        except Exception as e:  # pragma: no cover - dependency missing
            raise ImportError("Dash is required: pip install dash") from e

        from .render import markdown_to_html

        md_text = self.to_markdown()
        html_doc = markdown_to_html(md_text, title=self.title)
        external = self.dash_options.get("external_stylesheets")
        app = Dash(__name__, external_stylesheets=external)
        app.title = self.dash_options.get("page_title", f"EasyPour — {self.title}")

        preview_height = self.dash_options.get("preview_height", "70vh")
        tabs = self.dash_options.get("tabs", ["Report", "Markdown", "HTML", "PDF"])
        pdf_button_id: str | None = None
        pdf_download_id: str | None = None

        def _stable_id(*parts: str) -> str:
            h = hashlib.md5("||".join(parts).encode()).hexdigest()[:10]
            return f"mf_{h}"

        def _image_src(path: str) -> str:
            try:
                p = Path(path)
                if not p.exists():
                    return path
                data = base64.b64encode(p.read_bytes()).decode("ascii")
                mime, _ = mimetypes.guess_type(p.name)
                return f"data:{mime or 'image/png'};base64,{data}"
            except Exception:
                return path

        def _table_component(headers: list[str], rows: list[list[Any]]):
            if dash_table is not None:
                data = [dict(zip(headers, r, strict=False)) for r in rows]
                columns = [{"name": h, "id": h} for h in headers]
                return dash_table.DataTable(
                    columns=columns,
                    data=data,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "6px"},
                    style_header={"backgroundColor": "#f5f5f5", "fontWeight": "bold"},
                )
            # Fallback plain HTML table
            header_cells = [html.Th(h) for h in headers]
            body_rows = [html.Tr([html.Td(str(cell)) for cell in row]) for row in rows]
            return html.Table(
                [html.Thead(html.Tr(header_cells)), html.Tbody(body_rows)], className="mf-table"
            )

        def _image_component(img: Image, caption: str | None = None):
            width = None
            if isinstance(img.width, int):
                width = f"{img.width}px"
            elif isinstance(img.width, str):
                width = img.width
            fig_children = [
                html.Img(src=_image_src(img.path), style={"maxWidth": width or "100%"}),
            ]
            cap = caption or img.caption
            if cap:
                fig_children.append(html.Figcaption(cap))
            return html.Figure(fig_children, className="mf-image")

        def _render_section(sec: Section) -> html.Div:
            heading_map = {
                1: html.H1,
                2: html.H2,
                3: html.H3,
                4: html.H4,
                5: html.H5,
            }
            heading_cls = heading_map.get(sec.level, html.H6)
            children: list[Any] = [heading_cls(sec.title)]
            for idx, blk in enumerate(sec.blocks):
                children.extend(_render_block(sec, blk, idx))
            return html.Div(children, className=f"mf-section level-{sec.level}")

        def _render_block(sec: Section, blk: Any, index: int) -> list[Any]:
            elems: list[Any] = []
            if isinstance(blk, str):
                elems.append(dcc.Markdown(blk, className="mf-text"))
            elif isinstance(blk, Table):
                tbl = _table_component(blk.headers, blk.rows)
                elems.append(html.Div(tbl, className="mf-table-wrap"))
            elif isinstance(blk, Image):
                elems.append(_image_component(blk))
            elif isinstance(blk, InteractiveFigure):
                if blk.plotly_figure:
                    elems.append(
                        html.Div(
                            dcc.Graph(figure=blk.plotly_figure, config={"responsive": True}),
                            className="mf-interactive-plot",
                        )
                    )
                    if blk.figure.caption:
                        elems.append(html.Figcaption(blk.figure.caption, className="mf-figcaption"))
                else:
                    elems.append(_image_component(blk.figure.image, blk.figure.caption))
            elif isinstance(blk, PageBreak):
                elems.append(html.Hr(className="mf-page-break"))
            elif isinstance(blk, DataFrameBlock):
                try:
                    import pandas as pd  # type: ignore

                    df = blk.data if hasattr(blk.data, "columns") else pd.DataFrame(blk.data)
                    headers = list(df.columns)
                    rows = df.values.tolist()
                    elems.append(_table_component(headers, rows))
                except Exception:
                    elems.append(dcc.Markdown(blk.caption or "(DataFrame unavailable)"))
            elif isinstance(blk, Section):
                elems.append(_render_section(blk))
            elif hasattr(blk, "to_markdown"):
                try:
                    elems.append(dcc.Markdown(blk.to_markdown()))
                except Exception:
                    elems.append(dcc.Markdown(str(blk)))
            return elems

        report_children = [_render_section(sec) for sec in self.sections] or [
            html.Div(dcc.Markdown("(No sections defined yet.)"), className="mf-empty")
        ]

        tab_components: list[Any] = []
        tab_value = None
        for name in tabs:
            value = name.lower()
            if tab_value is None:
                tab_value = value
            if name == "Report":
                tab_components.append(
                    dcc.Tab(label="Report", value=value, children=report_children)
                )
            elif name == "Markdown":
                tab_components.append(
                    dcc.Tab(
                        label="Markdown",
                        value=value,
                        children=[
                            dcc.Textarea(
                                value=md_text,
                                readOnly=True,
                                style={
                                    "width": "100%",
                                    "height": preview_height,
                                    "fontFamily": "monospace",
                                },
                            )
                        ],
                    )
                )
            elif name == "HTML":
                tab_components.append(
                    dcc.Tab(
                        label="HTML Preview",
                        value=value,
                        children=[
                            html.Iframe(
                                srcDoc=html_doc,
                                style={
                                    "width": "100%",
                                    "height": preview_height,
                                    "border": "1px solid #ddd",
                                },
                            )
                        ],
                    )
                )
            elif name == "PDF":
                pdf_button_id = _stable_id("pdf", "button")
                pdf_download_id = _stable_id("pdf", "download")
                tab_components.append(
                    dcc.Tab(
                        label="PDF",
                        value=value,
                        children=[
                            html.P("Generate a PDF on demand. ReportLab must be installed."),
                            html.Button("Download PDF", id=pdf_button_id, n_clicks=0),
                            dcc.Download(id=pdf_download_id),
                        ],
                    )
                )
        layout_body: list[Any] = []
        if self.dash_css_text:
            layout_body.append(html.Style(self.dash_css_text))
        layout_body.append(html.H1(self.title))
        if self.author:
            layout_body.append(html.P(f"Author: {self.author}", className="mf-author"))
        if tab_components:
            layout_body.append(dcc.Tabs(id="mf-tabs", value=tab_value, children=tab_components))
        else:
            layout_body.extend(report_children)

        app.layout = html.Div(layout_body, style={"padding": "1rem 2rem"})

        if pdf_button_id and pdf_download_id:

            @app.callback(
                Output(pdf_download_id, "data"),
                Input(pdf_button_id, "n_clicks"),
                prevent_initial_call=True,
            )
            def _download_pdf(n_clicks):  # type: ignore[misc]
                if not n_clicks:
                    from dash.exceptions import PreventUpdate  # type: ignore

                    raise PreventUpdate
                import tempfile
                from pathlib import Path as _Path

                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                    self.write_pdf(tmp.name)
                    data = _Path(tmp.name).read_bytes()

                from dash.dcc import send_bytes  # type: ignore

                def _write_bytes(buffer):
                    buffer.write(data)

                return send_bytes(_write_bytes, "report.pdf")

        return app
