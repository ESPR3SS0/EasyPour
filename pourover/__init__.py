from __future__ import annotations

from pathlib import Path

"""Public API exports for PourOver.

Supports both legacy short helper names (b/i/u/link) and the newer explicit
names (bold/italic/underline/url) depending on what the core module provides.
"""

# file: pourover/__init__.py
from .render import markdown_to_html, markdown_to_pdf
from .ieee import IEEETemplate

# Core types are stable
from .core import Report, Section, Table, Image, code  # type: ignore

# Expose helpers with compatibility for either naming style
try:  # new explicit names
    from .core import bold, italic, underline, url  # type: ignore
except Exception:  # legacy short aliases
    bold = None  # type: ignore[assignment]
    italic = None  # type: ignore[assignment]
    underline = None  # type: ignore[assignment]
    url = None  # type: ignore[assignment]

try:  # legacy names
    from .core import b, i, u, link  # type: ignore
except Exception:
    # derive legacy from new if available
    b = bold  # type: ignore[assignment]
    i = italic  # type: ignore[assignment]
    u = underline  # type: ignore[assignment]
    link = url  # type: ignore[assignment]

__all__ = [
    "Report",
    "Section",
    "Table",
    "Image",
    "code",
    "markdown_to_html",
    "markdown_to_pdf",
    "IEEETemplate",
]

# Add whichever helper names are available
for name in ("bold", "italic", "underline", "url", "b", "i", "u", "link"):
    if globals().get(name) is not None:
        __all__.append(name)


def tex_to_png(formula: str, out_dir: Path | str, dpi: int = 220) -> Path:
    """Lazily expose the math renderer without importing matplotlib until needed."""
    from .mathstub import tex_to_png as _tex_to_png

    return _tex_to_png(formula, Path(out_dir), dpi=dpi)


__all__.append("tex_to_png")

# Backfill newer Section helpers if the core version doesn't provide them
def _attach_section_helpers():
    # bullets
    if not hasattr(Section, "add_bullets"):
        def add_bullets(self, items):
            lst = "\n".join(f"- {str(x)}" for x in items)
            if lst:
                self.blocks.append(lst)
            return self
        Section.add_bullets = add_bullets  # type: ignore[attr-defined]

    # checklist
    if not hasattr(Section, "add_checklist"):
        def add_checklist(self, items):
            lst = "\n".join(f"- [{'x' if done else ' '}] {text}" for (text, done) in items)
            if lst:
                self.blocks.append(lst)
            return self
        Section.add_checklist = add_checklist  # type: ignore[attr-defined]

    # codeblock
    if not hasattr(Section, "add_codeblock"):
        def add_codeblock(self, code_text, language=None):
            max_ticks = 3
            run = 0
            for ch in code_text:
                if ch == "`":
                    run += 1
                    if run > max_ticks:
                        max_ticks = run
                else:
                    run = 0
            fence = "`" * (max_ticks if max_ticks > 3 else 3)
            if "```" in code_text and len(fence) == 3:
                fence = "````"
            lang = language or ""
            block = f"{fence}{lang}\n{code_text}\n{fence}"
            self.blocks.append(block)
            return self
        Section.add_codeblock = add_codeblock  # type: ignore[attr-defined]

    # strikethrough paragraph
    if not hasattr(Section, "add_strikethrough"):
        try:
            from .core import strikethrough as _st  # type: ignore
        except Exception:
            def _st(text):
                return f"~~{text}~~"
        def add_strikethrough(self, text):
            self.blocks.append(_st(text))
            return self
        Section.add_strikethrough = add_strikethrough  # type: ignore[attr-defined]

_attach_section_helpers()
