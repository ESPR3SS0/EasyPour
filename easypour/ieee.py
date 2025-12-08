"""IEEE-flavored PDF template helpers."""

from __future__ import annotations

from dataclasses import dataclass

from reportlab.lib import colors

from .render import PDFTemplate


@dataclass
class IEEETemplate(PDFTemplate):
    """Preset tuned for IEEE-style two-column papers.

    - First page defaults to a single column for title/abstract.
    - Subsequent pages use two columns with Times fonts and tighter spacing.
    - Running headers/page numbers are enabled by default.
    """

    layout: str = "two"
    running_header_left: str = "PREPRINT"
    running_header_right: str = "EasyPour"
    include_header: bool = True
    include_page_numbers: bool = True
    first_page_single_column: bool = True

    def __post_init__(self) -> None:
        """Populate sensible IEEE defaults for layout, fonts, and headers."""
        # Layout defaults
        self.layout = self.layout or "two"
        if self.first_page_single_column:
            self.first_page_layout = "single"
        if not self.column_gap:
            self.column_gap = 18.0

        # Typography defaults
        self.font = "Times-Roman"
        self.font_bold = "Times-Bold"
        self.mono_font = "Courier"
        self.base_font_size = 9.5
        self.h1 = 20.0
        self.h2 = 12.0
        self.h3 = 10.0
        self.section_spacing = 0.4
        self.figure_prefix = "Fig."
        self.table_prefix = "TABLE"
        self.figure_caption_style.setdefault("font", self.font)
        self.figure_caption_style.setdefault("font_size", self.base_font_size - 1)
        self.table_caption_style.setdefault("font", self.font_bold)
        self.table_caption_style.setdefault("font_size", self.base_font_size - 1)

        # Heading tweaks (center title, uppercase section labels)
        self.heading_overrides.setdefault(1, {"alignment": "center"})
        self.heading_overrides.setdefault(2, {"spacing_before": 6, "spacing_after": 4})
        self.heading_overrides.setdefault(3, {"spacing_before": 4, "spacing_after": 2})

        # Paragraph tweaks (slightly denser body text)
        self.paragraph_overrides.setdefault("space_after", 3)

        def header(canv, template: PDFTemplate, page_num: int) -> None:
            if not self.include_header or page_num == 1:
                return
            canv.saveState()
            canv.setFont(self.font_bold, max(self.base_font_size - 1, 8))
            canv.setFillColor(colors.grey)
            width, _ = template._page_size_tuple()
            canv.drawString(
                template.margin_left,
                template.page_size[1] - template.margin_top + 12,
                self.running_header_left,
            )
            right_text = self.running_header_right
            canv.drawRightString(
                width - template.margin_right,
                template.page_size[1] - template.margin_top + 12,
                right_text,
            )
            canv.restoreState()

        def footer(canv, template: PDFTemplate, page_num: int) -> None:
            if not self.include_page_numbers:
                return
            canv.saveState()
            canv.setFont(self.font, max(self.base_font_size - 1, 8))
            canv.setFillColor(colors.grey)
            width, _ = template._page_size_tuple()
            canv.drawCentredString(width / 2, template.margin_bottom / 2, str(page_num))
            canv.restoreState()

        self.header_fn = header
        self.footer_fn = footer


__all__ = ["IEEETemplate"]
