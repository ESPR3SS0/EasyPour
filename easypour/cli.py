"""Cyclopts-based CLI for EasyPour.

Falls back to a tiny internal parser if Cyclopts is unavailable, so tests and
basic usage still work without extra installs.
"""

# file: easypour/cli.py
import importlib.util
import pathlib
import sys
from typing import Optional

from .render import markdown_to_html, markdown_to_pdf

def _load_builder(py_path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("report_builder", str(py_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    if not hasattr(mod, "build_report"):
        print("Builder module must define build_report() -> (markdown:str or report_obj)", file=sys.stderr)
        sys.exit(2)
    return mod.build_report()


def _guess_md_title(md_text: str) -> Optional[str]:
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading
    return None

def _run(
    builder: Optional[pathlib.Path],
    md: Optional[pathlib.Path],
    pdf: Optional[pathlib.Path],
    html: Optional[pathlib.Path],
    from_md: Optional[pathlib.Path],
) -> int:
    if from_md and builder:
        print("Use either --builder or --from-md, not both.", file=sys.stderr)
        return 2

    report_obj = None
    title_hint: Optional[str] = None
    md_text: Optional[str] = None
    if from_md:
        md_text = from_md.read_text(encoding="utf-8")
        title_hint = _guess_md_title(md_text)
    else:
        if not builder:
            print("--builder or --from-md is required", file=sys.stderr)
            return 2
        obj = _load_builder(builder)
        if hasattr(obj, "to_markdown"):
            md_text = obj.to_markdown()
            report_obj = obj if hasattr(obj, "write_pdf") else None
            title_hint = getattr(obj, "title", None)
        elif isinstance(obj, str):
            md_text = obj
        else:
            print("build_report() should return a Report or Markdown string.", file=sys.stderr)
            return 2

    assert md_text is not None
    if md:
        md.write_text(md_text, encoding="utf-8")
    if html:
        html.write_text(markdown_to_html(md_text), encoding="utf-8")
    if pdf:
        if not report_obj:
            try:
                markdown_to_pdf(md_text, str(pdf), title=title_hint or "Report")
            except ImportError:
                print(
                    "PDF output from Markdown requires WeasyPrint; install EasyPour[weasy] or pip install weasyprint.",
                    file=sys.stderr,
                )
                return 2
        else:
            report_obj.write_pdf(str(pdf))
    return 0


def _fallback_parse(argv: list[str]) -> dict[str, Optional[str]]:
    """Very small flag parser for --builder/--from-md/--md/--html/--pdf/--css.

    Avoids argparse; keeps CLI usable without Cyclopts installed.
    """
    flags = {"builder", "from-md", "md", "html", "pdf"}
    out: dict[str, Optional[str]] = {k.replace("-", "_"): None for k in flags}
    it = iter(argv)
    for tok in it:
        if tok.startswith("--"):
            key = tok[2:]
            if key in flags:
                try:
                    out[key.replace("-", "_")] = next(it)
                except StopIteration:
                    print(f"Flag --{key} expects a value", file=sys.stderr)
                    out["_error"] = "1"
                    break
    return out


def main():
    # Try Cyclopts first
    try:
        from cyclopts import App  # type: ignore

        app = App(name="easypour", help="Build Markdown/HTML/PDF reports.")

        @app.default
        def build(
            builder: Optional[pathlib.Path] = None,
            md: Optional[pathlib.Path] = None,
            pdf: Optional[pathlib.Path] = None,
            html: Optional[pathlib.Path] = None,
            from_md: Optional[pathlib.Path] = None,
        ) -> None:
            code = _run(builder, md, pdf, html, from_md)
            if code:
                sys.exit(code)

        app()
        return
    except Exception:
        # Minimal fallback parser
        args = _fallback_parse(sys.argv[1:])
        if args.get("_error"):
            sys.exit(2)
        code = _run(
            builder=pathlib.Path(args["builder"]) if args.get("builder") else None,
            md=pathlib.Path(args["md"]) if args.get("md") else None,
            pdf=pathlib.Path(args["pdf"]) if args.get("pdf") else None,
            html=pathlib.Path(args["html"]) if args.get("html") else None,
            from_md=pathlib.Path(args["from_md"]) if args.get("from_md") else None,
        )
        if code:
            sys.exit(code)


if __name__ == "__main__":
    main()
