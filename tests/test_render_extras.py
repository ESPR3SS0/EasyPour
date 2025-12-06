# tests/test_render_extras.py
import re
from easypour import markdown_to_html


def test_markdown_to_html_with_extra_css_and_text_url():
    md = "Visit https://example.com and ~~old~~ text."
    extra = "body { background: #fff; }"
    html = markdown_to_html(md, title="Extras", extra_css=extra)
    # extra CSS merged into style block
    assert "<style>" in html and "background: #fff;" in html
    # bare URLs currently remain as text; ensure present in HTML output
    assert "https://example.com" in html
    # strikethrough renders with s/del tag depending on renderer
    assert re.search(r"<(s|del)>old</(s|del)>", html) is not None
