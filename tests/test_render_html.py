# tests/test_render_html.py
import re
from easypour import markdown_to_html

def test_markdown_to_html_contains_inline_css_and_body():
    md = "# Title\n\nParagraph\n\n|A|B|\n|---|---|\n|1|2|\n"
    html = markdown_to_html(md, title="X")
    assert "<!doctype html>" in html.lower()
    assert "<style>" in html and "</style>" in html
    assert "<table" in html and "</table>" in html
    assert "<h1>Title</h1>" in html
    # basic sanity that our default CSS variables are present
    assert "--text:" in html
