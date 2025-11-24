---
title: Examples
---

# Examples

This repository includes several end‑to‑end examples in `examples/`:

- `simple/` — minimal report with one section and a table
- `complex/` — multiple sections, bullets, checklist, code block, image
- `streamlit/` — Streamlit app that previews Markdown/HTML and offers a PDF download (optional matplotlib plot toggle)
- `streamlit/matplotlib_app.py` — Streamlit demo that adds matplotlib figures via `add_matplotlib()`
- `streamlit/interactive_plots.py` — Minimal Streamlit app showing Matplotlib → Plotly interactivity
- `streamlit/sliders_multi.py` — Multiple interactive matplotlib plots (zoom/pan) with narrative sections
- `streamlit/time_series_sliders.py` — Two time-series plots upgraded to interactive Plotly views
- `streamlit/pdf_with_customization.py` — Custom Streamlit hooks and one-click PDF export to disk
- `pdf/complex_builder.py` — CLI-style complex report that exports Markdown + PDF
- `pdf/multi_figs_tables.py` — Multiple figures and tables with both PDF paths (Markdown + object)
- `pdf/ieee_builder.py` — End-to-end IEEE two-column builder using `IEEETemplate`
- `dash/` — Dash app that renders the report HTML in an iframe
- `dash/advanced_app.py` — Advanced Dash app with controls, slider, tabs, and downloads
- `dash/interactive_plots.py` — Dash app that upgrades Matplotlib figures to interactive Plotly graphs

Run the Simple Builder
```bash
python -m mochaflow.cli --builder examples/simple/builder.py --md examples/out/simple.md
```

Complex Builder (with optional image)

Multi Figures + Tables (two PDF paths)
```bash
python examples/pdf/multi_figs_tables.py
# Writes examples/out/multi.md, examples/out/multi_md.pdf, examples/out/multi_obj.pdf
```
```bash
python -m mochaflow.cli --builder examples/complex/builder.py --md examples/out/complex.md
```

Streamlit Demo (now one-liner)
```bash
streamlit run examples/streamlit/app.py
```

Streamlit + Matplotlib Demo
```bash
streamlit run examples/streamlit/matplotlib_app.py
```

Streamlit Interactive Plots (single report)
```bash
streamlit run examples/streamlit/interactive_plots.py
```

Streamlit Interactive Plots (multi-plot)
```bash
streamlit run examples/streamlit/sliders_multi.py
```

Streamlit Interactive Plots (time-series)
```bash
streamlit run examples/streamlit/time_series_sliders.py
```

Streamlit Custom + PDF Export
```bash
streamlit run examples/streamlit/pdf_with_customization.py
# PDF saved to examples/out/streamlit_custom.pdf (if ReportLab is installed)
```

Simple Full Workflow
```bash
python examples/playbook/simple_full.py
# Preview in Streamlit: streamlit run examples/playbook/simple_full.py -- --preview streamlit
# Preview in Dash: python examples/playbook/simple_full.py --preview dash
```

Complex PDF Export (non-Streamlit)
```bash
python examples/pdf/complex_builder.py
# Writes examples/out/complex.md and examples/out/complex.pdf
```

Advanced Full Workflow
```bash
python examples/playbook/advanced_full.py
# Preview in Streamlit: streamlit run examples/playbook/advanced_full.py -- --preview streamlit
# Preview in Dash: python examples/playbook/advanced_full.py --preview dash
```

IEEE Template Sample
```bash
python examples/pdf/ieee_builder.py
# Writes examples/out/ieee_sample.(md|pdf)
```

Dash Demo (uses `Report.to_dash_app()`)
```bash
python examples/dash/app.py
# open http://127.0.0.1:8050/
```

Advanced Dash Demo
```bash
python examples/dash/advanced_app.py
# open http://127.0.0.1:8050/
```

Dash Interactive Plots Demo
```bash
python examples/dash/interactive_plots.py
# open http://127.0.0.1:8050/
```

## Full Workflow Examples

### Simple Report (examples/playbook/simple_full.py)

1. **Write Markdown/PDF:** `python examples/playbook/simple_full.py`  
   - Outputs land in `examples/out/simple_full.(md|pdf)`.
2. **Preview in Streamlit:** `streamlit run examples/playbook/simple_full.py -- --preview streamlit`  
   - The script builds the report and calls `report.show_streamlit()` automatically.
3. **Preview in Dash:** `python examples/playbook/simple_full.py --preview dash`  
   - Starts a Dash server with tabs for Report/Markdown/HTML/PDF.

### Advanced Report (examples/playbook/advanced_full.py)

1. **Write Markdown/PDF (IEEE template):** `python examples/playbook/advanced_full.py`  
   - Uses `IEEETemplate` and saves outputs as `examples/out/advanced_full.(md|pdf)`.
2. **Preview in Streamlit:** `streamlit run examples/playbook/advanced_full.py -- --preview streamlit`
3. **Preview in Dash:** `python examples/playbook/advanced_full.py --preview dash`

Both scripts share the same command-line interface (`--preview streamlit|dash`), making it easy to jump from artifact generation to interactive previews.

One‑liner Streamlit Preview From a Script
```python
# my_app.py
from mochaflow import Report, Table

r = Report("Preview Me", author="You")
r.add_section("Hello").add_text("This is shown in Streamlit.")
r.add_section("Metrics").add_table(Table(headers=["A","B"], rows=[[1,2],[3,4]]))
r.show_streamlit()

# Run: streamlit run my_app.py
```

Matplotlib Convenience
```python
from mochaflow.core import Report
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(3, 2))
ax.plot([0, 1, 2], [0, 1, 0])
ax.set_title("Curve")

r = Report("Matplotlib Demo")
r.add_section("Figure").add_matplotlib(fig, out_dir="assets", filename="curve.png", caption="A curve", width="60%")
```

## Simple Example (source + walkthrough)

Source: `examples/simple/builder.py`

```python
from __future__ import annotations

from mochaflow import Report, Table


def build_report() -> Report:
    rpt = Report("Simple Example", author="Examples")
    s = rpt.add_section("Hello")
    s.add_text("This is a very small report.")
    s.add_table(Table(headers=["A", "B"], rows=[[1, 2], [3, 4]]))
    return rpt
```

What it does
- Creates a `Report` with a title and author.
- Adds a section titled `Hello`, with one paragraph of text.
- Adds a small `Table` (two columns, two rows).
- Returns the `Report` object. You can render it to Markdown/HTML/PDF or via the CLI builder flag.

CLI usage
- `python -m mochaflow.cli --builder examples/simple/builder.py --md examples/out/simple.md`

## Streamlit Example (source + walkthrough)

Source: `examples/streamlit/app.py`

```python
"""Streamlit example for MochaFlow.

Run:
  streamlit run examples/streamlit/app.py

This demo builds a small report and then delegates UI rendering to
`Report.show_streamlit()` which displays Markdown, an HTML preview, and a PDF
download button with sensible defaults.
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "mochaflow").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mochaflow.core import Report, Table, Image


def _make_demo_plot():
    """Create a tiny matplotlib figure for the demo (no heavy deps)."""
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None
    fig, ax = plt.subplots(figsize=(3.2, 2.0))
    ax.plot([0, 1, 2, 3], [0.0, 0.8, 0.3, 1.2], marker="o")
    ax.set_title("Demo Plot")
    ax.set_xlabel("Step")
    ax.set_ylabel("Value")
    fig.tight_layout()
    return fig


def build_report(
    include_table: bool,
    include_image: bool,
    include_plot: bool = False,
    include_dataframe: bool = False,
) -> Report:
    rpt = Report("Streamlit Demo", author="Examples")
    rpt.add_section("Summary").add_text(
        "This report was generated inside Streamlit.",
        "Toggle options in the sidebar to include extra content.",
    )
    if include_table:
        tbl = Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
            ]
        )
        rpt.add_section("Metrics").add_table(tbl)
    if include_image:
        # Use a placeholder; users can replace with a real path
        try:
            import streamlit as st  # imported here to avoid hard dependency on import
            placeholder_path = str(st.__file__)
        except Exception:
            placeholder_path = "./path/to/your/image.png"
        rpt.add_section("Artifacts").add_image_path(
            path=placeholder_path, alt="placeholder", caption="Replace with your image"
        )
    if include_plot:
        fig = _make_demo_plot()
        if fig is not None:
            rpt.add_section("Plot").add_matplotlib(
                fig,
                out_dir=".mochaflow_figs",
                filename="demo_plot.png",
                caption="A tiny demo plot",
                width="60%",
            )
        else:
            # Matplotlib not available; add a friendly note
            rpt.add_section("Plot").add_text("Matplotlib not installed; no plot shown.")
    if include_dataframe:
        try:
            import pandas as pd  # type: ignore
            df = pd.DataFrame(
                {"feature": ["f1", "f2", "f3"], "mean": [0.12, -0.03, 1.05], "std": [0.08, 0.14, 0.22]}
            )
            tbl = Table(headers=list(df.columns), rows=df.values.tolist())
            rpt.add_section("Pandas DataFrame").add_table(tbl)
        except Exception:
            rpt.add_section("Pandas DataFrame").add_text("pandas not installed; no DataFrame shown.")
    return rpt


if __name__ == "__main__":
    # Interactive toggles and preview using built-in helper
    try:
        import streamlit as st  # type: ignore
    except Exception:
        # If run outside `streamlit run`, silently build and exit
        rpt = build_report(include_table=True, include_image=False, include_plot=True)
        print(rpt.to_markdown())
    else:
        st.set_page_config(page_title="MochaFlow + Streamlit", layout="wide")
        st.title("MochaFlow + Streamlit")
        st.sidebar.header("Options")
        opt_table = st.sidebar.checkbox("Include table", value=True)
        opt_image = st.sidebar.checkbox("Include image placeholder", value=False)
        opt_plot = st.sidebar.checkbox("Include matplotlib plot", value=True)
        opt_df = st.sidebar.checkbox("Include pandas DataFrame", value=True)
        opt_interactive = st.sidebar.checkbox("Include interactive (plotly) view", value=True)
        rpt = build_report(opt_table, opt_image, opt_plot, opt_df)
        if opt_interactive:
            fig = _make_demo_plot()
            if fig is not None:
                rpt.add_section("Interactive Plot").add_matplotlib(
                    fig,
                    out_dir=".mochaflow_figs",
                    filename="interactive_demo.png",
                    caption="Zoom/pan in Streamlit via Plotly; rendered as PNG in Markdown/PDF.",
                    width="70%",
                    interactive=True,
                )
        rpt.show_streamlit(height=520)
```

What it does
- Builds a `Report` with optional sections: metrics table, placeholder image, matplotlib plot, and a pandas DataFrame.
- Uses `Report.show_streamlit()` to render four tabs:
  - Report: renders sections with native Streamlit widgets (headers, tables, images).
  - Markdown: shows the raw Markdown string for copy/paste or quick review.
  - HTML: renders full HTML preview; attempts to rewrite local image paths for iframe viewing.
  - PDF: provides a download button when ReportLab is installed.
- Demonstrates how `Section.add_matplotlib(..., interactive=True)` upgrades a Matplotlib figure to Plotly inside Streamlit/Dash (zoom, pan, hover) while keeping the PDF/Markdown output as a static image.

## Dash Example (source + walkthrough)

Source: `examples/dash/app.py`

```python
"""Dash example for MochaFlow.

Run:
  python examples/dash/app.py

Open http://127.0.0.1:8050/ in your browser.
"""
from __future__ import annotations

import pathlib, sys

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "mochaflow").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mochaflow.core import Report, Table


def build_report(include_table: bool) -> Report:
    rpt = Report("Dash Demo", author="Examples")
    rpt.add_section("Summary").add_text(
        "This report was generated inside Dash.",
        "Use the checkbox to include a table.",
    )
    if include_table:
        tbl = Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
            ]
        )
        rpt.add_section("Metrics").add_table(tbl)
    return rpt


if __name__ == "__main__":
    # Build a default report and render it using the built-in helper.
    app = build_report(include_table=True).to_dash_app()
    app.run_server(debug=True)
```

What it does
- Builds a `Report` similar to the Streamlit example.
- Uses `Report.to_dash_app()` to create a Dash application with tabs for:
  - Report: renders sections inline using Dash components (headers, tables, figures).
  - Markdown: read-only text area for the Markdown string.
  - HTML: preview inside an `<iframe>`.
  - PDF: on-demand download button (requires ReportLab).
- You can customize tab order/selection via `report.configure_dash(tabs=[...])` or extend the returned app layout as needed.
