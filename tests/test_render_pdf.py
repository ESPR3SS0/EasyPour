import pathlib

import pytest

from mochaflow import Report, Table, markdown_to_pdf
from mochaflow.render import PDFTemplate

pytestmark = pytest.mark.pdf


def test_markdown_to_pdf_roundtrip(tmp_path, ensure_pdf_capability):
    md = "# Title\n\nA para with **bold** and a table.\n\n|A|B|\n|---|---|\n|1|2|\n"
    out_pdf = tmp_path / "x.pdf"
    path = markdown_to_pdf(md, str(out_pdf), base_url=".")
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
