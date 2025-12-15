from __future__ import annotations

import pytest
from easypour import Report
from easypour.render import PDFTemplate
from hypothesis import given
from hypothesis import strategies as st


def _hex_color() -> st.SearchStrategy[str]:
    return st.text(alphabet="0123456789abcdef", min_size=6, max_size=6).map(lambda s: f"#{s}")


_color_keys = st.sampled_from(["color", "textColor", "text_color"])

heading_styles = st.dictionaries(
    keys=st.integers(min_value=1, max_value=6),
    values=st.builds(lambda key, color: {key: color}, _color_keys, _hex_color()),
    max_size=4,
)

paragraph_styles = st.dictionaries(
    keys=st.sampled_from(["color", "textColor", "text_color", "space_after"]),
    values=st.one_of(_hex_color(), st.integers(min_value=0, max_value=24)),
    max_size=2,
)


@given(heading=heading_styles, paragraph=paragraph_styles)
def test_configure_pdf_merges_heading_and_paragraph(heading, paragraph):
    rpt = Report("Styled")
    kwargs = {}
    if heading:
        kwargs["heading_overrides"] = heading
    if paragraph:
        kwargs["paragraph_overrides"] = paragraph
    if not kwargs:
        kwargs["pdf_style"] = {"font": "Helvetica"}  # ensure configure_pdf still invoked
    rpt.configure_pdf(**kwargs)
    tpl = PDFTemplate()
    rpt._apply_pdf_template_overrides(tpl, user_template=False)  # type: ignore[arg-type]
    for level, style in heading.items():
        for key, value in style.items():
            assert tpl.heading_overrides[level][key] == value
    for key, value in paragraph.items():
        assert tpl.paragraph_overrides[key] == value


@given(
    st.fixed_dictionaries(
        {
            "font": st.sampled_from(["Helvetica", "Courier"]),
            "base_font_size": st.integers(min_value=8, max_value=24),
        }
    )
)
def test_configure_pdf_direct_attrs_apply(overrides):
    rpt = Report("Attrs")
    rpt.configure_pdf(**overrides)
    tpl = PDFTemplate(font="Helvetica")
    rpt._apply_pdf_template_overrides(tpl, user_template=False)  # type: ignore[arg-type]
    for attr, value in overrides.items():
        assert getattr(tpl, attr) == value


def _non_int_text():
    return st.text(min_size=1).filter(lambda s: _fails_int_cast(s))


def _fails_int_cast(value: str) -> bool:
    try:
        int(value)
        return False
    except ValueError:
        return True


@given(_non_int_text())
def test_heading_overrides_with_non_int_keys_raise(key):
    rpt = Report("Invalid")
    rpt.configure_pdf(heading_overrides={key: {"color": "#fff"}})
    tpl = PDFTemplate()
    with pytest.raises(ValueError):
        rpt._apply_pdf_template_overrides(tpl, user_template=False)  # type: ignore[arg-type]
