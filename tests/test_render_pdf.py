import pathlib
import warnings

import pytest
from easypour import Report, Table
from easypour.render import PDFTemplate

pytestmark = pytest.mark.pdf


def test_report_write_pdf_default(tmp_path, ensure_pdf_capability):
    rpt = Report("Default PDF Test")
    rpt.add_section("Intro").add_text("A para with **bold** and a table.")
    rpt.add_section("Data").add_table(Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]]))
    out_pdf = tmp_path / "x.pdf"
    path = rpt.write_pdf(str(out_pdf))
    pdf_path = pathlib.Path(path)
    assert pdf_path.exists()
    data = pdf_path.read_bytes()
    assert data[:4] == b"%PDF"
    assert len(data) > 200


def test_report_write_pdf_with_template(tmp_path, ensure_pdf_capability):
    rpt = Report("Template Demo", author="EasyPour")
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


def test_configure_pdf_overrides_template_warns(tmp_path, ensure_pdf_capability):
    def custom_header(canv, template, page_num):
        canv.setFont(template.font_bold, template.base_font_size)
        canv.drawString(
            template.margin_left, template.page_size[1] - template.margin_top / 2, f"p.{page_num}"
        )

    rpt = Report("Configured Template")
    rpt.add_section("Body").add_text("Configured template override demo.")
    rpt.configure_pdf(
        margin_left=36, figure_caption_style={"font": "Courier"}, header_fn=custom_header
    )
    template = PDFTemplate(margin_left=72, figure_caption_style={"font": "Helvetica"})
    out_pdf = tmp_path / "configured.pdf"
    with pytest.warns(UserWarning) as record:
        rpt.write_pdf(str(out_pdf), template=template)
    messages = [str(r.message) for r in record]
    assert any("margin_left" in msg for msg in messages)
    assert any("header_fn" in msg for msg in messages)
    assert template.margin_left == 36
    assert template.header_fn is custom_header
    assert template.figure_caption_style["font"] == "Courier"


def test_configure_pdf_without_template_no_warning(tmp_path, ensure_pdf_capability):
    rpt = Report("Configured Defaults")
    rpt.add_section("Only Section").add_text("Margins + fonts via configure_pdf().")
    rpt.configure_pdf(margins=(40, 40, 54, 54), base_font_size=14)
    out_pdf = tmp_path / "configured_default.pdf"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rpt.write_pdf(str(out_pdf))
    assert not any("configure_pdf" in str(w.message) for w in caught)
    assert out_pdf.exists()
