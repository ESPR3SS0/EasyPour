# EasyPour Examples

This folder contains a few end‑to‑end examples that generate Markdown/HTML/PDF and show interactive previews.

Examples:
- `simple` — minimal report with one section, a table
- `complex` — multiple sections, bullets, checklist, code block, image

Interactive:
- `streamlit/` — Streamlit app driven by `Report.show_streamlit()`
- `dash/` — Dash app created via `Report.to_dash_app()`

Generate outputs to `examples/out/` by running:

```
python examples/generate_examples.py
```

Notes
- Uses the ReportLab backend for PDF generation.
- The tiny image used in examples is embedded from base64 into `examples/assets/tiny.png` during generation.

Run the interactive examples
- Streamlit: `streamlit run examples/streamlit/app.py`
- Dash: `python examples/dash/app.py` then open http://127.0.0.1:8050/
