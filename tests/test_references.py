import pytest

from mochaflow.core import Report, Section, Table, TableBlock


def test_citations_ordering():
    rpt = Report("Citations Demo")
    rpt.add_reference("smith19", "Smith et al., 'Demo Paper', 2019.")
    rpt.add_reference("jones21", "Jones, 'Another Paper', 2021.")

    first = rpt.cite("smith19")
    second = rpt.cite("jones21")
    again = rpt.cite("smith19")

    assert first == "[1]"
    assert second == "[2]"
    assert again == "[1]"  # stable numbering

    sec = rpt.ensure_references_section()
    rendered = "\n".join(str(block) for block in sec.blocks if isinstance(block, str))
    assert "[1] Smith et al." in rendered
    assert "[2] Jones" in rendered


def test_section_table_numbering():
    table = Table(headers=["A"], rows=[[1]])
    sec = Section("Data")
    sec.add_table(table, caption="Metrics", label="tab:metrics", numbered=True)
    block = sec.blocks[0]
    assert isinstance(block, TableBlock)
    assert block.label == "tab:metrics"
    assert block.numbered is True
