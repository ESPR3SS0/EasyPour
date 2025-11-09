# tests/test_section_lists_codeblocks.py
from mochaflow.core import Section
from importlib import import_module


def test_section_bullets():
    s = Section("Bullets").add_bullets(["one", "two", "three"])
    md = s.to_markdown()
    assert "## Bullets" in md
    assert "- one" in md and "- two" in md and "- three" in md


def test_section_checklist():
    items = [("todo", False), ("done", True)]
    s = Section("Tasks").add_checklist(items)
    md = s.to_markdown()
    assert "## Tasks" in md
    assert "- [ ] todo" in md
    assert "- [x] done" in md


def test_section_codeblock_with_language():
    s = Section("Code").add_codeblock("print(1)", language="python")
    md = s.to_markdown()
    assert "## Code" in md
    assert "```python" in md
    assert "print(1)" in md
    assert md.count("```") >= 2


def test_section_codeblock_handles_backticks_inside():
    code = "here are ticks:\n```\ninside\n```\nend"
    s = Section("Ticks").add_codeblock(code, language="text")
    md = s.to_markdown()
    # fence should be at least four backticks due to inner triple
    assert "````" in md
    assert code in md


def test_section_strikethrough_paragraph():
    s = Section("Strike").add_strikethrough("old text")
    md = s.to_markdown()
    assert "## Strike" in md
    assert "~~old text~~" in md
