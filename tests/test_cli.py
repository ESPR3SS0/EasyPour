# tests/test_cli.py
import os
import subprocess
import sys
import textwrap
import pathlib
import pytest

pytestmark = pytest.mark.cli

PYTHON = sys.executable

def test_cli_from_md_to_html(tmp_path):
    md_path = tmp_path / "r.md"
    html_path = tmp_path / "r.html"
    md_path.write_text("# T\n\nHi\n", encoding="utf-8")

    # python -m pourover.cli --from-md ... --html ...
    cmd = [PYTHON, "-m", "pourover.cli", "--from-md", str(md_path), "--html", str(html_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr
    assert html_path.exists()
    assert "<h1>T</h1>" in html_path.read_text(encoding="utf-8")

def test_cli_with_builder_outputs_md(tmp_path):
    builder = tmp_path / "builder.py"
    out_md = tmp_path / "out.md"
    builder.write_text(textwrap.dedent("""
        from pourover import Report
        def build_report():
            rpt = Report("CLI Report", author="You")
            rpt.add_section("S").add_text("Hello")
            return rpt
    """), encoding="utf-8")

    cmd = [PYTHON, "-m", "pourover.cli", "--builder", str(builder), "--md", str(out_md)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr
    assert out_md.exists()
    content = out_md.read_text(encoding="utf-8")
    assert "# CLI Report" in content
    assert "## S" in content
    assert "Hello" in content

@pytest.mark.pdf
def test_cli_from_md_to_pdf(tmp_path, ensure_weasy_capability):
    """`--from-md` can emit PDFs via WeasyPrint when installed."""
    md_path = tmp_path / "r.md"
    pdf_path = tmp_path / "r.pdf"
    md_path.write_text("# PDF\n\n**ok**\n", encoding="utf-8")
    cmd = [PYTHON, "-m", "pourover.cli", "--from-md", str(md_path), "--pdf", str(pdf_path)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr
    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"
