import base64
import pathlib

import pytest
from reportlab.platypus import Spacer

from mochaflow import Report
from mochaflow.render import PDFTemplate

pytestmark = pytest.mark.pdf

_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def _write_tiny_png(path: pathlib.Path) -> None:
    path.write_bytes(_TINY_PNG)


def test_pdf_mixins_roundtrip(tmp_path, ensure_pdf_capability):
    img = tmp_path / "tiny.png"
    _write_tiny_png(img)

    rpt = Report("Mixins Demo", author="MochaFlow")
    sec = rpt.add_section("Layout")
    sec.add_two_column_layout(["Left text"], ["Right text"], gap=18)
    sec.add_vertical_space(24)
    sec.add_absolute_image(img, x=72, y=640, width=36, height=36)
    sec.add_floating_image(img, align="right", width=28, caption="Float caption")
    sec.add_pdf_flowable(lambda template: Spacer(1, template.base_font_size))
    sec.add_double_space()
    sec.add_new_page()

    out_pdf = tmp_path / "mixins.pdf"
    path = rpt.write_pdf(str(out_pdf), template=PDFTemplate())
    pdf_path = pathlib.Path(path)
    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"
