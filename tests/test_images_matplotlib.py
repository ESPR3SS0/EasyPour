import pathlib
import pytest

from mochaflow.core import Report, Section, Image
from mochaflow import markdown_to_pdf
import pytest

# Skip this module if matplotlib is not available
try:
    import matplotlib.pyplot as plt  # noqa: F401
except Exception as _e:  # pragma: no cover
    pytest.skip(f"matplotlib unavailable: {_e}", allow_module_level=True)


def test_add_image_path_convenience(tmp_png):
    s = Section("S").add_image_path(tmp_png, alt="dot", caption="tiny", width="40%")
    md = s.to_markdown()
    assert "![dot](" in md
    assert "figcaption" in md and "tiny" in md
    assert "style=\"width:40%;\"" in md


def _make_mpl_plot():
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.plot([0, 1], [0, 1])
    ax.set_title("t")
    return fig


def test_add_matplotlib_image_markdown(tmp_path):
    fig = _make_mpl_plot()
    s = Section("S").add_matplotlib(fig, out_dir=tmp_path, filename="plot.png", alt="p", caption="cap")
    md = s.to_markdown()
    assert "plot.png" in md
    assert (tmp_path / "plot.png").exists()


@pytest.mark.pdf
def test_add_matplotlib_image_weasy_pdf(tmp_path, ensure_pdf_capability):
    fig = _make_mpl_plot()
    rpt = Report("R")
    rpt.add_section("S").add_matplotlib(fig, out_dir=tmp_path, filename="plot.png", alt="p")
    out_pdf = tmp_path / "r.pdf"
    markdown_to_pdf(rpt.to_markdown(), str(out_pdf), base_url=str(tmp_path))
    data = out_pdf.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 200
