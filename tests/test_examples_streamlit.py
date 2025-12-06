import importlib
import pathlib
import pytest

from pourover import markdown_to_html


def has_streamlit():
    try:
        import streamlit  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not has_streamlit(), reason="streamlit not installed")
def test_streamlit_example_builds_report_and_html():
    mod = importlib.import_module("examples.streamlit.app")
    rpt = mod.build_report(include_table=True, include_image=False)
    md = rpt.to_markdown()
    assert "# Streamlit Demo" in md
    assert "## Metrics" in md
    # Round-trip to HTML
    html = markdown_to_html(md, title=rpt.title)
    assert "<!doctype html>" in html.lower()


@pytest.mark.skipif(not has_streamlit(), reason="streamlit not installed")
def test_streamlit_example_with_image_includes_caption():
    mod = importlib.import_module("examples.streamlit.app")
    rpt = mod.build_report(include_table=False, include_image=True)
    md = rpt.to_markdown()
    # The example uses a caption string we can assert on
    assert "Replace with your image" in md
