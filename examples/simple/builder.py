from __future__ import annotations

from easypour import Report, Table


def build_report() -> Report:
    rpt = Report("Simple Example", author="Examples")
    s = rpt.add_section("Hello")
    s.add_text("This is a very small report.")
    s.add_table(Table(headers=["A", "B"], rows=[[1, 2], [3, 4]]))
    return rpt
