# tests/test_core_edge_cases.py
import os

from easypour import Image, Report, Table


def test_table_to_markdown_empty_headers():
    t = Table(headers=[], rows=[[1, 2]])
    assert t.to_markdown() == ""


def test_table_from_dicts_empty_iterable():
    t = Table.from_dicts([])
    assert t.headers == []
    assert t.rows == []


def test_table_str_coercion_for_numbers():
    t = Table(headers=["A", "B"], rows=[[1, 2.5]])
    md = t.to_markdown().strip().splitlines()
    assert md[2] in {"| 1 | 2.5 |"}


def test_image_caption_only(tmp_png):
    im = Image(path=str(tmp_png), alt="dot", caption="cap")
    md = im.to_markdown()
    assert md.startswith("<figure")
    assert "figcaption" in md
    assert 'style="width:' not in md


def test_image_width_only(tmp_png):
    im = Image(path=str(tmp_png), alt="dot", width="50%")
    md = im.to_markdown()
    assert md.startswith("<figure")
    assert 'style="width:50%;"' in md
    assert "figcaption" not in md


def test_report_meta_and_date_and_no_author(tmp_path):
    rpt = Report(title="X", author=None, date_str="2020-01-02", meta={"draft": True, "v": 3})
    md = rpt.to_markdown()
    # Front matter contains date and meta
    assert "date: 2020-01-02" in md
    assert "draft: True" in md and "v: 3" in md
    # Body contains top-level title and italic date line
    assert "# X" in md
    assert "*2020-01-02*" in md
    # No author line when author is None
    assert "**Author:**" not in md


def test_write_markdown_returns_absolute_path(tmp_path):
    rpt = Report("Abs")
    out = tmp_path / "z.md"
    abs_path = rpt.write_markdown(str(out))
    assert os.path.isabs(abs_path)
    assert os.path.samefile(abs_path, out)
