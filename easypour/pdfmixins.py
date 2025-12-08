"""PDF-specific helper directives for advanced layout control.

These lightweight dataclasses are attached to sections/reports so the
ReportLab renderer can inject custom Flowables (two-column layouts, absolute
images, manual spacing, etc.) without the caller needing to poke into the
rendering internals.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlowableDirective:
    """Wrapper around a callable that returns one or more ReportLab Flowables."""

    factory: Callable[[Any], Any]


@dataclass
class TwoColumnDirective:
    """Render two independent block lists side-by-side."""

    left: list[Any] = field(default_factory=list)
    right: list[Any] = field(default_factory=list)
    gap: float = 12.0  # points between columns


@dataclass
class AbsoluteImageDirective:
    """Place an image at an absolute position on the page (ReportLab coords)."""

    path: str
    x: float
    y: float
    width: float | None = None
    height: float | None = None
    page: int | None = None  # reserve for future (specific page targeting)


@dataclass
class FloatingImageDirective:
    """Floating image with alignment and optional caption/padding."""

    path: str
    align: str = "left"  # left/right/center
    width: float | None = None
    height: float | None = None
    caption: str | None = None
    padding: float = 6.0


@dataclass
class VerticalSpaceDirective:
    """Insert vertical whitespace measured in points."""

    height: float


@dataclass
class DoubleSpaceDirective:
    """Shortcut for inserting a spacer equivalent to one extra line of text."""

    active: bool = True


__all__ = [
    "FlowableDirective",
    "TwoColumnDirective",
    "AbsoluteImageDirective",
    "FloatingImageDirective",
    "VerticalSpaceDirective",
    "DoubleSpaceDirective",
]
