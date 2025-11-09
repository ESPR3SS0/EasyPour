# tests/test_cli_errors.py
import subprocess
import sys
import textwrap
import pathlib
import pytest

pytestmark = pytest.mark.cli

PYTHON = sys.executable


def test_cli_mutually_exclusive_flags(tmp_path):
    md_path = tmp_path / "in.md"
    html_path = tmp_path / "out.html"
    builder = tmp_path / "builder.py"
    md_path.write_text("# T\n", encoding="utf-8")
    builder.write_text("def build_report():\n    return '# T'\n", encoding="utf-8")

    cmd = [
        PYTHON,
        "-m",
        "mochaflow.cli",
        "--from-md",
        str(md_path),
        "--builder",
        str(builder),
        "--html",
        str(html_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 2
    assert "Use either --builder or --from-md" in res.stderr


def test_cli_builder_missing_function(tmp_path):
    builder = tmp_path / "builder.py"
    builder.write_text("# no build_report here\n", encoding="utf-8")
    out_md = tmp_path / "out.md"
    cmd = [PYTHON, "-m", "mochaflow.cli", "--builder", str(builder), "--md", str(out_md)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 2
    assert "Builder module must define build_report()" in res.stderr


def test_cli_builder_returns_string_to_html(tmp_path):
    builder = tmp_path / "builder.py"
    out_html = tmp_path / "out.html"
    # write without leading indentation/newline to avoid IndentationError
    builder.write_text(
        "def build_report():\n    return \"# H\\n\\nHi\"\n",
        encoding="utf-8",
    )
    cmd = [PYTHON, "-m", "mochaflow.cli", "--builder", str(builder), "--html", str(out_html)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, res.stderr
    assert out_html.exists()
    assert "<h1>H</h1>" in out_html.read_text(encoding="utf-8")


def test_cli_builder_returns_wrong_type(tmp_path):
    builder = tmp_path / "builder.py"
    out_md = tmp_path / "out.md"
    builder.write_text(textwrap.dedent(
        """
        def build_report():
            return 123
        """
    ), encoding="utf-8")
    cmd = [PYTHON, "-m", "mochaflow.cli", "--builder", str(builder), "--md", str(out_md)]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 2
    assert "should return a Report or Markdown string" in res.stderr
