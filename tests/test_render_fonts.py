import pytest

import easypour.render as render_mod
from easypour import Report
from easypour.render import PDFTemplate


def _mock_font_stack(monkeypatch, existing=None):
    existing = set(existing or ())
    registered = {}

    def fake_get_font(name):
        if name in registered:
            return registered[name]
        if name in existing:
            return object()
        raise KeyError(name)

    def fake_register(font_obj):
        registered[font_obj.name] = font_obj

    class DummyTTFont:
        def __init__(self, name, path):
            self.name = name
            self.path = path

    monkeypatch.setattr(render_mod, "TTFont", DummyTTFont)
    monkeypatch.setattr(render_mod.pdfmetrics, "getFont", fake_get_font)
    monkeypatch.setattr(render_mod.pdfmetrics, "registerFont", fake_register)
    return registered


def _make_font_file(tmp_path, name="Custom"):
    font_path = tmp_path / f"{name}.ttf"
    font_path.write_bytes(b"fake-font-data")
    return font_path


def test_pdf_template_registers_font_from_path(tmp_path, monkeypatch):
    registered = _mock_font_stack(monkeypatch)
    font_path = _make_font_file(tmp_path, "MyFont")
    template = PDFTemplate(font=str(font_path))

    template._prepare_fonts()

    assert template.font.startswith("MyFont")
    assert template.font in registered
    assert registered[template.font].path == str(font_path)


def test_font_files_mapping_used_for_registration(tmp_path, monkeypatch):
    registered = _mock_font_stack(monkeypatch)
    font_path = _make_font_file(tmp_path, "BrandSans")
    template = PDFTemplate(font="BrandSans")
    template.font_files["BrandSans"] = str(font_path)

    template._prepare_fonts()

    assert template.font == "BrandSans"
    assert "BrandSans" in registered
    assert registered["BrandSans"].path == str(font_path)


def test_font_name_collision_allocates_suffix(tmp_path, monkeypatch):
    registered = _mock_font_stack(monkeypatch, existing={"Collide"})
    font_path = _make_font_file(tmp_path, "Collide")
    template = PDFTemplate(font=str(font_path))

    template._prepare_fonts()

    assert template.font != "Collide"
    assert template.font.startswith("Collide")
    assert template.font in registered
    assert registered[template.font].path == str(font_path)


def test_configure_pdf_merges_font_files(tmp_path, monkeypatch):
    registered = _mock_font_stack(monkeypatch)
    font_path = _make_font_file(tmp_path, "DocuSans")
    rpt = Report("Fonts FTW")
    rpt.configure_pdf(font="DocuSans", font_files={"DocuSans": str(font_path)})
    template = PDFTemplate()

    rpt._apply_pdf_template_overrides(template, user_template=False)
    template._prepare_fonts()

    assert template.font == "DocuSans"
    assert "DocuSans" in registered
    assert registered["DocuSans"].path == str(font_path)
