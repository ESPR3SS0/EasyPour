import pathlib

import pytest

from mochaflow import Report, Table
from mochaflow.render import PDFTemplate

pytestmark = pytest.mark.pdf


def test_report_write_pdf_default(tmp_path, ensure_pdf_capability):
    rpt = Report("Default PDF Test")
    rpt.add_section("Intro").add_text("A para with **bold** and a table.")
    rpt.add_section("Data").add_table(
        Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])
    )
    out_pdf = tmp_path / "x.pdf"
    path = rpt.write_pdf(str(out_pdf))
    pdf_path = pathlib.Path(path)
    assert pdf_path.exists()
    data = pdf_path.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 200


def test_report_write_pdf_with_template(tmp_path, ensure_pdf_capability):
    rpt = Report("Template Demo", author="MochaFlow")
    rpt.add_section("Summary").add_text("Hello **world**!", "Some _italic_ text.")
    rpt.add_section("Metrics").add_table(
        Table(headers=["Metric", "Value"], rows=[["Accuracy", "92.8%"], ["F1", "91.5%"]])
    )
    template = PDFTemplate(font="Helvetica", base_font_size=11, accent_color="#e76f51")
    out_pdf = tmp_path / "templated.pdf"
    path = rpt.write_pdf(str(out_pdf), template=template)
    pdf_path = pathlib.Path(path)
    assert pdf_path.exists()
    data = pdf_path.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 200
