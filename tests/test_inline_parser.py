# tests/test_inline_parser.py
import pytest

from mochaflow.inline import parse_inline


def text_of(runs):
    return "".join(r.text for r in runs)


def test_parse_bold_italic_code_link_underline_and_plain():
    s = "A **bold** and *italic* word, `code`, a [link](https://ex.com), and <u>under</u>."
    runs = parse_inline(s)
    # Find styled runs
    has_bold = any(r.bold and r.text == "bold" for r in runs)
    has_italic = any(r.italic and r.text == "italic" for r in runs)
    has_code = any(r.code and r.text == "code" for r in runs)
    has_link = any(r.link == "https://ex.com" and r.text == "link" for r in runs)
    has_underline = any(getattr(r, "underline", False) and r.text == "under" for r in runs)
    assert has_bold and has_italic and has_code and has_link and has_underline


def test_parse_footnote_marker_runs():
    s = "Value is high[^note1] in this dataset."
    runs = parse_inline(s)
    # Expect a run with a footnote key in the sequence
    assert any(getattr(r, "footnote_key", None) == "note1" for r in runs)
