import pathlib
import warnings

import pytest
from easypour import Report, Table
from easypour.render import PDFTemplate
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

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


# ---------------- Hypothesis-based fuzzing -----------------


def _ascii_text(min_size: int = 1, max_size: int = 20) -> st.SearchStrategy[str]:
    alphabet = st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters=["`"])
    return st.text(alphabet=alphabet, min_size=min_size, max_size=max_size)


@st.composite
def _section_data(draw):
    title = draw(_ascii_text(1, 24))
    paragraphs = draw(st.lists(_ascii_text(0, 80), min_size=1, max_size=3))
    include_table = draw(st.booleans())
    table_dims = None
    if include_table:
        cols = draw(st.integers(min_value=1, max_value=3))
        rows = draw(st.integers(min_value=1, max_value=4))
        table_dims = (cols, rows)
    include_nested = draw(st.booleans())
    return {
        "title": title,
        "paragraphs": paragraphs,
        "table": table_dims,
        "nested": include_nested,
    }


@st.composite
def _report_data(draw):
    title = draw(_ascii_text(1, 40))
    sections = draw(st.lists(_section_data(), min_size=1, max_size=3))
    return {"title": title, "sections": sections}


@st.composite
def _configure_kwargs(draw):
    kwargs: dict[str, object] = {}
    if draw(st.booleans()):
        kwargs["base_font_size"] = draw(st.integers(min_value=8, max_value=18))
    if draw(st.booleans()):
        margins = tuple(draw(st.integers(20, 80)) for _ in range(4))
        kwargs["margins"] = margins
    if draw(st.booleans()):
        kwargs["heading_overrides"] = {
            2: {"color": draw(st.sampled_from(["#222222", "#993300", "#0055aa"]))}
        }
    if draw(st.booleans()):
        kwargs["paragraph_overrides"] = {
            "color": draw(st.sampled_from(["#111111", "#444444", "#666666"]))
        }
    if draw(st.booleans()):
        runs = draw(
            st.lists(
                st.tuples(
                    st.sampled_from(["single", "two"]), st.integers(min_value=1, max_value=3)
                ),
                min_size=1,
                max_size=2,
            )
        )
        kwargs["page_layouts"] = runs
    return kwargs


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(report=_report_data(), template_kwargs=_configure_kwargs())
def test_pdf_render_randomized(tmp_path, tmp_png, ensure_pdf_capability, report, template_kwargs):
    rpt = Report(report["title"])
    for sec_payload in report["sections"]:
        sec = rpt.add_section(sec_payload["title"])
        for paragraph in sec_payload["paragraphs"]:
            sec.add_text(paragraph or "(empty)")
        if sec_payload["table"]:
            cols, rows = sec_payload["table"]
            headers = [f"C{i}" for i in range(cols)]
            body = [[f"{r}-{c}" for c in range(cols)] for r in range(rows)]
            sec.add_table(Table(headers=headers, rows=body))
        if sec_payload["nested"]:
            nested = sec.add_section("Nested")
            nested.add_text("Nested body")
    # Include a consistent image to cover that code path
    rpt.sections[0].add_image_path(tmp_png)
    if template_kwargs:
        rpt.configure_pdf(**template_kwargs)
    out = tmp_path / "fuzz.pdf"
    pdf_path = pathlib.Path(rpt.write_pdf(str(out)))
    data = pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 200
