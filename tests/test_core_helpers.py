# tests/test_core_helpers.py
from importlib import import_module

core = import_module("easypour.core")
# Support both the new long names and legacy short aliases without eager defaults
bold = getattr(core, "bold", None) or core.b
italic = getattr(core, "italic", None) or core.i
underline = getattr(core, "underline", None) or core.u
code = core.code
url = getattr(core, "url", None) or core.link


def test_bold():
    assert bold("x") == "**x**"


def test_italic():
    assert italic("x") == "*x*"


def test_underline_html():
    assert underline("x") == "<u>x</u>"


def test_code_inline():
    assert code("print(1)") == "`print(1)`"


def test_link():
    assert url("site", "https://ex.com") == "[site](https://ex.com)"
