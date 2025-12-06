from __future__ import annotations

import base64
import sys
import pathlib
import importlib.util


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easypour.core import Report  # noqa: E402


def ensure_assets() -> pathlib.Path:
    assets = ROOT / "examples" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    tiny = assets / "tiny.png"
    if not tiny.exists():
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
            "ASsJTYQAAAAASUVORK5CYII="
        )
        tiny.write_bytes(base64.b64decode(png_b64))
    return tiny


def load_builder(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("example_builder", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def can_reportlab() -> bool:
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        return True
    except Exception:
        return False


def write_all(name: str, rpt: Report, out_dir: pathlib.Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{name}.md"
    pdf_path = out_dir / f"{name}.pdf"
    

    # Markdown
    md_abs = rpt.write_markdown(str(md_path))
    print(f"[ok] markdown: {md_abs}")

    # PDF via Report.write_pdf (ReportLab backend)
    if can_reportlab():
        try:
            rpt.write_pdf(str(pdf_path))
            print(f"[ok] pdf: {pdf_path}")
        except Exception as e:
            print(f"[fail] pdf: {e}")
    else:
        print("[skip] pdf: ReportLab unavailable")


def run():
    examples_root = ROOT / "examples"
    out_dir = examples_root / "out"
    tiny = ensure_assets()

    # simple
    simple_mod = load_builder(examples_root / "simple" / "builder.py")
    rpt = simple_mod.build_report()
    write_all("simple", rpt, out_dir=out_dir)

    # complex
    complex_mod = load_builder(examples_root / "complex" / "builder.py")
    rpt = complex_mod.build_report(str(tiny))
    write_all("complex", rpt, out_dir=out_dir)

    # IEEE example removed (legacy borb backend)


if __name__ == "__main__":
    run()
