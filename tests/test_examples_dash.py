import importlib
import pytest

from pourover import markdown_to_html


def has_dash():
    try:
        import dash  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not has_dash(), reason="dash not installed")
def test_dash_example_builds_report_and_html():
    mod = importlib.import_module("examples.dash.app")
    rpt = mod.build_report(include_table=True, include_interactive=True)
    md = rpt.to_markdown()
    assert "# Dash Demo" in md
    assert "## Metrics" in md
    html = markdown_to_html(md, title=rpt.title)
    assert "<!doctype html>" in html.lower()


@pytest.mark.skipif(not has_dash(), reason="dash not installed")
def test_report_to_dash_app_produces_layout():
    mod = importlib.import_module("examples.dash.app")
    rpt = mod.build_report(include_table=True, include_interactive=True)
    app = rpt.to_dash_app()
    assert app.layout is not None
