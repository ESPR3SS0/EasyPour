import io

import easypour.render as render_mod
import pytest
from easypour.core import Image as CoreImage
from easypour.core import Table as CoreTable
from easypour.render import PDFTemplate, _image, _image_size_from_hints, _ScaledFlowable, _table
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import Table as RLTable


def _mock_image_reader(monkeypatch, size):
    class DummyReader:
        def __init__(self, path):
            self.path = path
            self._size = size

        def getSize(self):
            return self._size

    monkeypatch.setattr(render_mod, "ImageReader", DummyReader)
    monkeypatch.setattr("reportlab.lib.utils.ImageReader", DummyReader)


def test_image_size_autoscales_large_bitmap(monkeypatch):
    _mock_image_reader(monkeypatch, (2400, 1800))
    template = PDFTemplate(
        page_size=(400, 400),
        margin_left=20,
        margin_right=20,
        margin_top=20,
        margin_bottom=20,
    )

    width, height = _image_size_from_hints("oversized.png", template)

    max_w, max_h = template.frame_bounds()
    assert max_w == pytest.approx(360.0)
    assert max_h == pytest.approx(360.0)
    assert width == pytest.approx(max_w)
    assert height == pytest.approx(270.0)


def test_image_size_autoscale_uses_column_frame_bounds(monkeypatch):
    _mock_image_reader(monkeypatch, (600, 300))
    template = PDFTemplate(
        page_size=(400, 500),
        margin_left=40,
        margin_right=40,
        margin_top=40,
        margin_bottom=40,
        layout="two",
        column_gap=20,
    )

    width, height = _image_size_from_hints("chart.png", template, width_hint="200%")

    frame_w, frame_h = template.frame_bounds()
    assert frame_w == pytest.approx(150.0)
    assert frame_h == pytest.approx(420.0)
    assert width == pytest.approx(frame_w)
    assert height == pytest.approx(75.0)


def test_image_size_autoscale_clamps_height_hint(monkeypatch):
    _mock_image_reader(monkeypatch, (50, 50))
    template = PDFTemplate(
        page_size=(520, 420),
        margin_left=30,
        margin_right=30,
        margin_top=30,
        margin_bottom=30,
    )

    width, height = _image_size_from_hints(
        "tall.png",
        template,
        width_hint=200,
        height_hint="800px",
    )

    frame_w, frame_h = template.frame_bounds()
    assert frame_w == pytest.approx(460.0)
    assert frame_h == pytest.approx(360.0)
    assert height == pytest.approx(frame_h)
    assert width == pytest.approx(90.0)


def test_image_size_autoscale_can_be_disabled(monkeypatch):
    _mock_image_reader(monkeypatch, (400, 400))
    template = PDFTemplate(autoscale_images=False, margin_left=10, margin_right=10)

    width, height = _image_size_from_hints(
        "manual.png",
        template,
        width_hint="1000px",
        height_hint="800px",
    )

    assert width == pytest.approx(1000.0)
    assert height == pytest.approx(800.0)


def test_image_size_invalid_hints_fall_back_to_original(monkeypatch):
    _mock_image_reader(monkeypatch, (640, 480))
    template = PDFTemplate(autoscale_images=False)
    width, height = _image_size_from_hints(
        "bad.png",
        template,
        width_hint="0px",
        height_hint=-5,
    )
    assert width == pytest.approx(640.0)
    assert height == pytest.approx(480.0)


def test_image_size_zero_width_infers_from_height(monkeypatch):
    _mock_image_reader(monkeypatch, (800, 400))
    template = PDFTemplate(autoscale_images=False)
    width, height = _image_size_from_hints(
        "bad.png",
        template,
        width_hint=0,
        height_hint=200,
    )
    assert height == pytest.approx(200.0)
    assert width == pytest.approx(400.0)


def _sample_table(num_cols: int = 6, rows: int = 5, **style) -> CoreTable:
    headers = [f"C{i}" for i in range(num_cols)]
    body = [[f"{r}-{c}" for c in range(num_cols)] for r in range(rows)]
    return CoreTable(headers=headers, rows=body, pdf_style=style)


def test_table_autoscale_wraps_to_frame_bounds():
    template = PDFTemplate(
        page_size=(520, 640),
        margin_left=36,
        margin_right=36,
        margin_top=48,
        margin_bottom=48,
        layout="two",
        column_gap=18,
    )
    wide_table = _sample_table(num_cols=10)
    table_flowable = _table(wide_table, template)

    assert isinstance(table_flowable, _ScaledFlowable)
    frame_w, frame_h = template.frame_bounds()
    buf = io.BytesIO()
    canv = pdf_canvas.Canvas(buf)
    wrapped_w, wrapped_h = table_flowable.wrapOn(canv, frame_w, frame_h)
    assert wrapped_w <= frame_w + 1e-3
    assert wrapped_h <= frame_h + 1e-3


def test_table_autoscale_can_be_disabled():
    table_flowable = _table(_sample_table(), PDFTemplate(autoscale_tables=False))
    assert isinstance(table_flowable, RLTable)


def test_table_autoscale_shrinks_wide_custom_widths():
    template = PDFTemplate(page_size=(500, 600), margin_left=40, margin_right=40)
    tbl = _sample_table(num_cols=4, rows=3, col_widths=[220] * 4)
    flowable = _table(tbl, template)
    assert isinstance(flowable, _ScaledFlowable)
    buf = io.BytesIO()
    canv = pdf_canvas.Canvas(buf)
    frame_w, frame_h = template.frame_bounds()
    wrapped_w, wrapped_h = flowable.wrapOn(canv, frame_w, frame_h)
    assert wrapped_w <= frame_w + 1e-6
    assert wrapped_h <= frame_h + 1e-6


def test_table_autoscale_leaves_huge_tables_to_split():
    template = PDFTemplate(page_size=(500, 600), margin_left=40, margin_right=40)
    tbl = _sample_table(num_cols=3, rows=200)
    flowable = _table(tbl, template)
    assert isinstance(flowable, RLTable)


def test_image_flowable_shrinks_to_runtime_frame(monkeypatch):
    _mock_image_reader(monkeypatch, (1000, 600))
    template = PDFTemplate()
    block = CoreImage(path="fake.png")
    image_flow = _image(block, template)[0]
    buf = io.BytesIO()
    canv = pdf_canvas.Canvas(buf)
    wrapped_w, wrapped_h = image_flow.wrapOn(canv, 200, 500)
    assert wrapped_w == pytest.approx(200.0)
    # When height budget is tiny, we still report the full height so the flowable moves to the next page.
    _, tall_h = image_flow.wrapOn(canv, 200, 40)
    assert tall_h > 40
