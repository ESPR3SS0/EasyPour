---
title: Troubleshooting
---

# Troubleshooting

PDF export fails or looks odd

- Ensure ReportLab is installed: `pip install reportlab`.
- Check that image paths are correct and accessible from the working directory used when calling `Report.write_pdf`.
- Very large images may need explicit sizing; prefer using `Image(..., width="60%")` or similar.

CLI: builder not found or wrong return type

- Your builder module must define `build_report()`.
- It should return either a `Report` or a Markdown string.
- If both `--from-md` and `--builder` are provided, the CLI exits with an error — they are mutually exclusive.

Markdown contains triple backticks inside code blocks

- Use `Section.add_codeblock(...)`. It automatically picks a fence length that is longer than any run of backticks inside your code to avoid conflicts.

Inline underline rendering

- Markdown does not have native underline; EasyPour uses HTML `<u>…</u>` for underline to remain compatible across renderers.

Verifying installation and PDF capability

- Run tests if available: `pytest -q`
- Skip PDF tests when ReportLab is not present: `pytest -q -m "not pdf"`

AttributeError: 'Report' object has no attribute 'show_streamlit'

- You are likely importing an older installed EasyPour. Ensure you have the updated package:
  - In a venv: `pip install -e .` from the repo root, then restart your process.
  - Or uninstall any older install first: `pip uninstall -y EasyPour && pip install -e .`
- Verify what Python is importing:
  - `python -c "import easypour; from easypour import Report; print(easypour.__file__); print(hasattr(Report, 'show_streamlit'))"`
- When running the bundled examples, they prefer the local repo package automatically. For your own scripts outside the repo, install the package in your environment.
