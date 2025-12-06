"""Advanced Dash example for PourOver.

Run:
  python examples/dash/advanced_app.py

Open http://127.0.0.1:8050/ in your browser.

Features
- Controls: include table, include plot, slider for slope m
- Builds a PourOver Report and renders HTML in an iframe
- Shows Markdown in a code block
- Download buttons for Markdown and HTML via dcc.Download
"""
from __future__ import annotations

import base64
import io
import pathlib
import re
import sys
from typing import Optional

from dash import Dash, dcc, html, Input, Output, State

# Prefer the local repository package when running examples from source
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if (_ROOT / "pourover").exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pourover.core import Report, Table
from pourover import markdown_to_html


def _make_plot_png_bytes(m: float) -> Optional[bytes]:
    try:
        import numpy as np  # type: ignore
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None

    rng = np.random.default_rng(0)
    x = rng.normal(0, 1.0, size=160)
    y = 0.8 * x + rng.normal(0, 0.35, size=160)

    fig, ax = plt.subplots(figsize=(3.6, 2.4))
    ax.scatter(x, y, s=12, alpha=0.85, label="data")
    x_min, x_max = float(np.min(x)), float(np.max(x))
    xs = np.array([x_min, x_max])
    ax.plot(xs, m * xs, color="#d62728", label=f"y={m:.2f}x")
    ax.set_title("Scatter + slope overlay")
    ax.legend()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    return buf.getvalue()


def _html_inline_images(html_doc: str, img_bytes: Optional[bytes]) -> str:
    if not img_bytes:
        return html_doc
    # Replace the first <img ...> with a data URI (simple heuristic)
    b64 = base64.b64encode(img_bytes).decode("ascii")
    data_uri = f"data:image/png;base64,{b64}"
    return re.sub(r'src="([^"]+)"', f'src="{data_uri}"', html_doc, count=1)


def build_report(include_table: bool, include_plot: bool, m: float) -> tuple[Report, Optional[bytes]]:
    rpt = Report("Dash Advanced", author="Examples")
    rpt.add_section("Summary").add_text(
        "This report was generated inside Dash.",
        f"Use the controls to include a table and an image. Current slope m = {m:.2f} for the overlay.",
    )
    if include_table:
        tbl = Table.from_dicts(
            [
                {"Metric": "Accuracy", "Value": "92.8%"},
                {"Metric": "F1", "Value": "91.5%"},
                {"Metric": "ROC AUC", "Value": "0.962"},
            ]
        )
        rpt.add_section("Metrics").add_table(tbl)

    img_bytes = None
    if include_plot:
        img_bytes = _make_plot_png_bytes(m)
        if img_bytes:
            # Add a placeholder image tag in Markdown; we'll inline bytes in HTML later
            # We use a pseudo path so the Markdown contains an <img> we can replace.
            rst = rpt.add_section("Plot")
            rst.add_text("Below is a scatter plot with an overlay line y = m x.")
            rst.add_text(f"![plot](plot_{m:.2f}.png)")
        else:
            rpt.add_section("Plot").add_text("Matplotlib/numpy not installed; no plot shown.")

    return rpt, img_bytes


app = Dash(__name__)
app.title = "PourOver + Dash (Advanced)"

app.layout = html.Div(
    [
        html.H1("PourOver + Dash (Advanced)"),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Controls"),
                        dcc.Checklist(
                            id="opts",
                            options=[
                                {"label": "Include table", "value": "table"},
                                {"label": "Include plot", "value": "plot"},
                            ],
                            value=["table", "plot"],
                        ),
                        html.Div(style={"height": "8px"}),
                        html.Label("Slope m for overlay (y = m x)"),
                        dcc.Slider(id="slope", min=-2.0, max=2.0, step=0.05, value=0.8,
                                   tooltip={"always_visible": False}),
                        html.Div(style={"height": "8px"}),
                        html.Div(
                            [
                                html.Button("Download Markdown", id="dl-md-btn"),
                                dcc.Download(id="dl-md"),
                                html.Button("Download HTML", id="dl-html-btn", style={"marginLeft": "8px"}),
                                dcc.Download(id="dl-html"),
                            ]
                        ),
                    ],
                    style={"flex": "0 0 320px", "paddingRight": "1rem", "borderRight": "1px solid #ddd"},
                ),
                html.Div(
                    [
                        dcc.Tabs(
                            id="tabs",
                            value="tab-report",
                            children=[
                                dcc.Tab(label="Report", value="tab-report"),
                                dcc.Tab(label="Markdown", value="tab-md"),
                            ],
                        ),
                        html.Div(id="tab-content", style={"marginTop": "0.75rem"}),
                        dcc.Store(id="store-md"),
                        dcc.Store(id="store-html"),
                    ],
                    style={"flex": "1 1 auto", "paddingLeft": "1rem"},
                ),
            ],
            style={"display": "flex", "alignItems": "flex-start"},
        ),
    ],
    style={"padding": "1rem 2rem"},
)


@app.callback(
    Output("tab-content", "children"),
    Output("store-md", "data"),
    Output("store-html", "data"),
    Input("opts", "value"),
    Input("slope", "value"),
    Input("tabs", "value"),
)
def update_content(opts, slope, tab):
    include_table = "table" in (opts or [])
    include_plot = "plot" in (opts or [])
    rpt, img_bytes = build_report(include_table, include_plot, float(slope or 0.8))
    md = rpt.to_markdown()
    html_doc = markdown_to_html(md, title=rpt.title)
    html_doc = _html_inline_images(html_doc, img_bytes)

    if tab == "tab-md":
        return html.Pre(md, style={"whiteSpace": "pre-wrap"}), md, html_doc
    # Report tab: iframe of the HTML string
    return html.Iframe(srcDoc=html_doc, style={"width": "100%", "height": "70vh", "border": "1px solid #ddd"}), md, html_doc


@app.callback(
    Output("dl-md", "data", allow_duplicate=True),
    Input("dl-md-btn", "n_clicks"),
    State("store-md", "data"),
    prevent_initial_call=True,
)
def download_md(n, md):
    if not md:
        return dash.no_update  # type: ignore[name-defined]
    return dict(content=md, filename="report.md")


@app.callback(
    Output("dl-html", "data", allow_duplicate=True),
    Input("dl-html-btn", "n_clicks"),
    State("store-html", "data"),
    prevent_initial_call=True,
)
def download_html(n, html_doc):
    if not html_doc:
        return dash.no_update  # type: ignore[name-defined]
    return dict(content=html_doc, filename="report.html")


if __name__ == "__main__":
    app.run_server(debug=True)

