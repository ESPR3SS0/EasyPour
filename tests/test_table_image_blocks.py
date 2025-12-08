# tests/test_table_image_blocks.py
from easypour import Image, Section, Table


def test_table_markdown():
    t = Table(headers=["A", "B"], rows=[[1, 2], [3, 4]])
    md = t.to_markdown().strip().splitlines()
    assert md[0] == "| A | B |"
    assert md[1] == "| --- | --- |"
    assert md[2] == "| 1 | 2 |"
    assert md[3] == "| 3 | 4 |"


def test_table_from_dicts():
    rows = [{"A": 1, "B": 2}, {"A": 3, "B": 4}]
    t = Table.from_dicts(rows)
    assert t.headers == ["A", "B"]
    assert t.rows == [[1, 2], [3, 4]]


def test_image_markdown_plain(tmp_png):
    im = Image(path=str(tmp_png), alt="dot")
    md = im.to_markdown()
    assert md.startswith("![dot](") and md.endswith(")")


def test_image_markdown_with_caption_width(tmp_png):
    im = Image(path=str(tmp_png), alt="dot", caption="cap", width="60%")
    md = im.to_markdown()
    # HTML <figure> wrapper is used when caption/width provided
    assert md.startswith("<figure")
    assert "figcaption" in md


def test_section_add_blocks(sample_table, tmp_png):
    s = Section("Top")
    s.add_text("hello").add_table(sample_table).add_image(Image(str(tmp_png)))
    md = s.to_markdown()
    assert "## Top" in md
    assert "| Metric | Value |" in md
    assert "![](" in md or "![dot](" in md
