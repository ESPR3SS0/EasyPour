---
title: Contributing
---

# Contributing

Setup
- Create a virtualenv and install the package in editable mode: `pip install -e .`
- Install test and optional extras as needed: `pip install pytest reportlab matplotlib`

Tests
- Run all tests: `pytest -q`
- Quick, no-PDF/CLI tests: `pytest -q -m "not pdf and not cli"`

Lint/Format
- If using Ruff: `ruff check .` and `ruff format .`

Docs
- Install mkdocs: `pip install mkdocs`
- Preview: `mkdocs serve` (then open the shown URL)
- Build static site: `mkdocs build`

Examples
- Streamlit: `streamlit run examples/streamlit/app.py`
- Dash: `python examples/dash/app.py` then open http://127.0.0.1:8050/

Release Checklist (suggested)
- Bump version in `pyproject.toml`.
- Regenerate example outputs if you keep them under version control.
- Verify PDF generation locally (ReportLab installed).

Thanks for contributing! ✨
