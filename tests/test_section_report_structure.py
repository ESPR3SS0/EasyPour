# tests/test_section_report_structure.py
import re

from easypour import Report


def test_report_markdown_front_matter_and_title(sample_report):
    md = sample_report.to_markdown()
    # front matter fence and title presence
    assert md.startswith("---")
    assert "\n---\n" in md
    assert "# Weekly Model Analysis" in md
    assert "**Author:** ESPR3SS0" in md


def test_nested_sections_level_capping():
    rpt = Report("Nested")
    s = rpt.add_section("L2")
    s3 = s.add_section("L3")
    s4 = s3.add_section("L4")
    s5 = s4.add_section("L5")
    s6 = s5.add_section("L6")
    s6.add_section("L7")  # should clamp to h6
    md = rpt.to_markdown()
    # Count ATX headings by level using regex anchors
    assert len(re.findall(r"^## L2$", md, flags=re.M)) == 1
    assert len(re.findall(r"^### L3$", md, flags=re.M)) == 1
    assert len(re.findall(r"^#### L4$", md, flags=re.M)) == 1
    assert len(re.findall(r"^##### L5$", md, flags=re.M)) == 1
    assert len(re.findall(r"^###### L6$", md, flags=re.M)) == 1
    # L7 should also be rendered as h6 due to clamping
    assert len(re.findall(r"^###### L7$", md, flags=re.M)) == 1


def test_write_markdown(tmp_path, sample_report):
    out = tmp_path / "report.md"
    path = sample_report.write_markdown(str(out))
    assert out.exists()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "# Weekly Model Analysis" in content
