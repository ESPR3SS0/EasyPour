# tests/conftest.py
import base64
import os
import io
import pathlib
import sys
import importlib
import pytest

# Ensure tests import the local workspace pourover package, not an installed one.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if "pourover" in sys.modules:
    del sys.modules["pourover"]

from pourover import Report, Section, Table, Image

@pytest.fixture
def tmp_png(tmp_path):
    """Create a tiny PNG file for image tests/PDF render."""
    # 1x1 px transparent PNG
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
        "ASsJTYQAAAAASUVORK5CYII="
    )
    data = base64.b64decode(png_b64)
    p = tmp_path / "tiny.png"
    p.write_bytes(data)
    return p

@pytest.fixture
def sample_table():
    return Table(headers=["Metric", "Value"], rows=[["Accuracy", "92.8%"], ["F1", "91.5%"]])

@pytest.fixture
def sample_report(tmp_png, sample_table):
    rpt = Report(title="Weekly Model Analysis", author="ESPR3SS0", meta={"draft": True})
    s1 = rpt.add_section("Summary")
    s1.add_text("This is a **bold** summary.", "Second paragraph.")

    s2 = rpt.add_section("Metrics")
    s2.add_table(sample_table)

    s3 = rpt.add_section("Artifacts")
    s3.add_image(Image(path=str(tmp_png), alt="dot", caption="A tiny pixel", width="40px"))

    s4 = rpt.add_section("Notes")
    sub = s4.add_section("Deploy blockers")
    sub.add_text("Memory regression when enabling BN folding.")

    return rpt

def can_reportlab():
    """Check if ReportLab is functional (can render a trivial PDF)."""
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(100, 750, "ok")
        c.showPage()
        c.save()
        data = buf.getvalue()
        return isinstance(data, (bytes, bytearray)) and data[:4] == b"%PDF"
    except Exception:
        return False

def path_str(p):
    return str(pathlib.Path(p).resolve())

@pytest.fixture
def ensure_pdf_capability():
    if not can_reportlab():
        pytest.skip("ReportLab is not available.")


def can_weasy():
    """Check if WeasyPrint can produce a trivial PDF."""
    try:
        from weasyprint import HTML  # type: ignore
        buf = io.BytesIO()
        HTML(string="<p>ok</p>").write_pdf(buf)
        data = buf.getvalue()
        return isinstance(data, (bytes, bytearray)) and data[:4] == b"%PDF"
    except Exception:
        return False


@pytest.fixture
def ensure_weasy_capability():
    if not can_weasy():
        pytest.skip("WeasyPrint is not available.")


## borb backend fully removed; no borb fixtures
