import pathlib

from easypour import Report


def test_report_page_break_inserts_dummy_section(tmp_path, ensure_pdf_capability):
    rpt = Report("Break Demo")
    rpt.add_section("Intro").add_text("First page")
    rpt.add_page_break()
    rpt.add_section("Next").add_text("Second page")
    out = tmp_path / "break.pdf"
    path = pathlib.Path(rpt.write_pdf(str(out)))
    assert path.exists()
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
