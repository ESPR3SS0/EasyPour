import pytest
from easypour.ieee import IEEETemplate
from easypour.render import PDFTemplate, _heading
from reportlab.platypus import BaseDocTemplate


def test_register_layout_invoked():
    tpl = PDFTemplate(layout="custom")
    invoked = {"count": 0}

    def builder(template: PDFTemplate):
        invoked["count"] += 1
        return template._single_frames()

    tpl.register_layout("custom", builder)
    frames = tpl._frames_for_layout("custom")
    assert frames and invoked["count"] == 1


def test_heading_override_applied():
    tpl = PDFTemplate()
    tpl.heading_overrides[2] = {"font_size": 42}
    para = _heading("Hello", 2, tpl, None)
    assert para.style.fontSize == 42


def test_ieee_template_defaults():
    tpl = IEEETemplate()
    assert tpl.layout == "two"
    assert tpl.first_page_layout == "single"
    assert tpl.figure_prefix == "Fig."


def test_single_layout_uses_base_template(tmp_path):
    tpl = PDFTemplate()
    doc = tpl.make_document(str(tmp_path / "demo.pdf"))
    assert isinstance(doc, BaseDocTemplate)
    assert doc.pageTemplates
    frame = doc.pageTemplates[0].frames[0]
    width, height = tpl.frame_bounds()
    assert float(getattr(frame, "_width", frame.width)) == pytest.approx(width)
    assert float(getattr(frame, "_height", frame.height)) == pytest.approx(height)
