import pathlib

from easypour import Report, Table


def test_layout_block_renders_with_custom_layout(tmp_path, ensure_pdf_capability):
    rpt = Report("Layout Block Demo")
    sec = rpt.add_section("Intro")
    tbl = Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])
    sec.add_layout_block("two", tbl)
    rpt.add_section("Next").add_text("After block")
    out = tmp_path / "layout.pdf"
    path = pathlib.Path(rpt.write_pdf(str(out)))
    assert path.exists()
    assert path.read_bytes().startswith(b"%PDF")
