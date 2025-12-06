import pytest

from pourover import Report, tex_to_png


def _require_matplotlib():
    pytest.importorskip("matplotlib")


def test_tex_to_png_writes_file(tmp_path):
    _require_matplotlib()
    out_dir = tmp_path / "math"
    path = tex_to_png(r"E = mc^2", out_dir)
    assert path.exists()
    assert path.suffix == ".png"


def test_section_add_math_creates_image(tmp_path):
    _require_matplotlib()
    rpt = Report("Math Demo")
    sec = rpt.add_section("Equations")
    sec.add_math(r"\int_0^1 x^2 dx", out_dir=tmp_path, caption="Integral")
    files = list(tmp_path.glob("*.png"))
    assert files, "expected math image to be created"
    md = sec.to_markdown()
    assert any(f.name in md for f in files)
