# file: mdreport/ieee.py
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Dict, Any, List, Optional, Tuple
import copy
import re
from .core import Report, Section, Table as CoreTable, Image as CoreImage
from typing import Any as _Any
from pathlib import Path
from .render import DashboardMixin

FN_REF_RE = re.compile(r"\[\^(?P<key>[^\]]+)\]")
BLOCK_MATH_RE = re.compile(r"^\s*\$\$(?P<fm>.+?)\$\$\s*$", re.DOTALL)

@dataclass
class IEEEOptions:
    """High-level knobs for IEEE-like output."""
    two_column: bool = True
    show_lof: bool = False
    show_lot: bool = False
    running_header_left: str = "PREPRINT"
    running_header_right: str = "MochaFlow"
    references_title: str = "References"
    # mapping: citation key -> rendered reference string (IEEE-ish)
    bibliography: Dict[str, str] = field(default_factory=dict)
    footnotes: Dict[str, str] = field(default_factory=dict)
    math_dir: str = ".manymark_math"

@dataclass
class IEEETemplate(PDFTemplate, DashboardMixin):  # Inherits both PDF and dashboard capabilities
    """A thin preset over PDFTemplate aiming for IEEE-ish defaults."""
    page_size: Tuple[float, float] = (612.0, 792.0)  # US Letter in points
    margin_left: float = 54.0
    margin_right: float = 54.0
    margin_top: float = 60.0
    margin_bottom: float = 72.0
    layout: str = "two"  # default to two columns
    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    base_font_size: float = 9.5
    h1: float = 18.0
    h2: float = 11.0
    h3: float = 10.0
    def __post_init__(self):
        lh = self.margin_top - 24
        fh = self.margin_bottom - 36

        def header(page: _Any, frame: _Any, page_num: int):
            w = page.get_page_info().get_width()
            Paragraph(
                self.meta.get("running_header_left", "PREPRINT"),  # set via template.meta
                font=self.font, font_size=self.base_font_size - 1, text_color=X11Color("gray"),
                horizontal_alignment=Alignment.LEFT,
            ).paint(page, (self.margin_left, lh))  # Direct position calculation
            Paragraph(
                self.meta.get("running_header_right", "MochaFlow"),
                font=self.font, font_size=self.base_font_size - 1, text_color=X11Color("gray"),
                horizontal_alignment=Alignment.RIGHT,
            ).paint(page, (w - self.margin_right - 200, lh))  # Direct position calculation

        def footer(page: _Any, frame: _Any, page_num: int):
            w = page.get_page_info().get_width()
            Paragraph(
                str(page_num),
                font=self.font, font_size=self.base_font_size - 1, text_color=X11Color("gray"),
                horizontal_alignment=Alignment.CENTERED,
            ).paint(page, (w / 2 - 10, fh))  # Direct position calculation

        self.header_fn = header
        self.footer_fn = footer
        if not hasattr(self, "meta"):
            self.meta = {}  # type: ignore[attr-defined]
