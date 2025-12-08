"""Simple inline Markdown parser for EasyPour."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Run:
    """A span of text with associated inline formatting flags."""

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    code: bool = False
    link: str | None = None  # URL
    footnote_key: str | None = None  # e.g., "foo" from [^foo]


# Inline tokens: **bold**, *italic*, `code`, [text](url), <u>underline</u>, [^key]
RE_TOKEN = re.compile(
    r"(\*\*|__)(?P<bold>.+?)\1"  # **bold**
    r"|(\*|_)(?P<italic>.+?)\3"  # *italic*
    r"|`(?P<code>[^`]+?)`"  # `code`
    r"|\[(?P<link_text>.+?)\]\((?P<link_url>[^)]+)\)"  # [text](url)
    r"|<u>(?P<u_text>.+?)</u>"  # <u>underline</u>
    r"|\[\^(?P<fn_key>[^\]]+)\]",  # [^footnote]
    re.DOTALL,
)


def parse_inline(text: str) -> list[Run]:
    """Split text into formatting runs (bold, italics, links, etc.)."""
    runs: list[Run] = []
    i = 0
    for m in RE_TOKEN.finditer(text):
        if m.start() > i:
            runs.append(Run(text=text[i : m.start()]))
        if m.group("bold"):
            runs.append(Run(text=m.group("bold"), bold=True))
        elif m.group("italic"):
            runs.append(Run(text=m.group("italic"), italic=True))
        elif m.group("code"):
            runs.append(Run(text=m.group("code"), code=True))
        elif m.group("link_text"):
            runs.append(Run(text=m.group("link_text"), link=m.group("link_url")))
        elif m.group("u_text"):
            runs.append(Run(text=m.group("u_text"), underline=True))
        elif m.group("fn_key"):
            runs.append(Run(text="", footnote_key=m.group("fn_key")))
        i = m.end()
    if i < len(text):
        runs.append(Run(text=text[i:]))
    return _merge_adjacent(runs)


def _merge_adjacent(runs: list[Run]) -> list[Run]:
    """Combine consecutive runs with identical styling."""
    out: list[Run] = []
    for r in runs:
        if out and _same_style(out[-1], r):
            out[-1].text += r.text
        else:
            out.append(r)
    return out


def _same_style(a: Run, b: Run) -> bool:
    """Return True if two runs share identical formatting flags."""
    return (
        a.bold == b.bold
        and a.italic == b.italic
        and a.underline == b.underline
        and a.code == b.code
        and a.link == b.link
        and a.footnote_key is None
        and b.footnote_key is None
    )
