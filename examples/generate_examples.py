"""Build runnable example artifacts (Markdown/PDF) and copy them into docs."""

from __future__ import annotations

import base64
import importlib.util
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from easypour.core import Report  # noqa: E402
from easypour.ieee import IEEETemplate  # noqa: E402

DOCS_GENERATED = ROOT / "docs" / "examples" / "generated"
OUT_DIR = ROOT / "examples" / "out"


def ensure_assets() -> pathlib.Path:
    """Make sure the shared tiny PNG exists for non-IEEE examples."""
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
    """Dynamically import and return the module at the given path."""
    spec = importlib.util.spec_from_file_location("example_builder", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def can_reportlab() -> bool:
    """Return True if ReportLab is available in this environment."""
    try:
        return True
    except Exception:
        return False


def write_all(
    name: str,
    rpt: Report,
    out_dir: pathlib.Path,
    *,
    template: object | None = None,
) -> tuple[pathlib.Path, pathlib.Path | None]:
    """Write both Markdown and PDF outputs for a report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = pathlib.Path(rpt.write_markdown(str(out_dir / f"{name}.md")))
    print(f"[ok] markdown: {md_path}")

    pdf_path: pathlib.Path | None = None
    if can_reportlab():
        try:
            pdf_path = pathlib.Path(rpt.write_pdf(str(out_dir / f"{name}.pdf"), template=template))
            print(f"[ok] pdf: {pdf_path}")
        except Exception as exc:
            print(f"[fail] pdf: {exc}")
    else:
        print("[skip] pdf: ReportLab unavailable")
    return md_path, pdf_path


def copy_to_docs(*paths: pathlib.Path | None) -> None:
    """Copy generated artifacts into docs/examples/generated."""
    DOCS_GENERATED.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path and path.exists():
            shutil.copy2(path, DOCS_GENERATED / path.name)


def run():
    """Build each example report and duplicate the outputs for docs."""
    if DOCS_GENERATED.exists():
        shutil.rmtree(DOCS_GENERATED)
    DOCS_GENERATED.mkdir(parents=True, exist_ok=True)

    examples_root = ROOT / "examples"
    out_dir = OUT_DIR
    tiny = ensure_assets()

    # simple
    simple_mod = load_builder(examples_root / "simple" / "builder.py")
    md, pdf = write_all("simple", simple_mod.build_report(), out_dir=out_dir)
    copy_to_docs(md, pdf)

    # complex
    complex_mod = load_builder(examples_root / "complex" / "builder.py")
    md, pdf = write_all("complex", complex_mod.build_report(str(tiny)), out_dir=out_dir)
    copy_to_docs(md, pdf)

    # playbook / simple_full
    simple_full_mod = load_builder(examples_root / "playbook" / "simple_full.py")
    md, pdf = write_all("simple_full", simple_full_mod.build_report(), out_dir=out_dir)
    copy_to_docs(md, pdf)

    # IEEE sample
    ieee_mod = load_builder(examples_root / "pdf" / "ieee_builder.py")
    ieee_asset = None
    if hasattr(ieee_mod, "_ensure_asset"):
        try:
            ieee_asset = ieee_mod._ensure_asset()
        except FileNotFoundError as exc:
            print(f"[skip] ieee_sample: {exc}")
    if ieee_asset:
        ieee_template = IEEETemplate(
            running_header_left="IEEE PREPRINT",
            running_header_right="Sample Paper",
            include_page_numbers=True,
        )
        md, pdf = write_all(
            "ieee_sample",
            ieee_mod.build_report(ieee_asset),
            out_dir=out_dir,
            template=ieee_template,
        )
        copy_to_docs(md, pdf)


if __name__ == "__main__":
    run()
