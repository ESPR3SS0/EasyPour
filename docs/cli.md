---
title: CLI
---

# Command Line Interface

MochaFlow includes a simple CLI module that can:
- Convert an existing Markdown file to HTML
- Run a Python “builder” module that returns a `Report` (or Markdown string) and write outputs

Invocation
```bash
python -m mochaflow.cli [--from-md PATH | --builder PATH] [--md OUT.md] [--html OUT.html] [--pdf OUT.pdf]
```

Flags
- `--from-md PATH`: Read Markdown from the given file
- `--builder PATH`: Import the given Python file and call `build_report()`
  - The function should return either a `Report` or a Markdown `str`
- `--md OUT.md`: Write the Markdown string to a file
- `--html OUT.html`: Render HTML and write to a file
- `--pdf OUT.pdf`: Render a PDF via `Report.write_pdf` (only available when `build_report()` returns a `Report`)

Mutually Exclusive
- `--from-md` and `--builder` cannot be used together

Examples
Convert Markdown to HTML
```bash
python -m mochaflow.cli --from-md report.md --html report.html
```

Run a Python builder
```python
# builder.py
from mochaflow import Report
def build_report():
    r = Report("CLI Report", author="You")
    r.add_section("Hello").add_text("This was generated via the CLI.")
    return r
```

```bash
# Markdown
python -m mochaflow.cli --builder builder.py --md out.md
# HTML
python -m mochaflow.cli --builder builder.py --html out.html
# PDF
python -m mochaflow.cli --builder builder.py --pdf out.pdf
```

Notes
- The CLI prefers Cyclopts if installed, but falls back to a tiny internal parser to remain dependency-light.
- PDF output is only available when the builder returns a `Report`; `--from-md` cannot produce PDFs.
- Ensure images referenced by Markdown are accessible on disk when generating HTML.
