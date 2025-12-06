---
title: Streamlit Customization
---

# Streamlit Customization

PourOver lets you customize Streamlit previews in two ways:

- Via `Report` APIs (options, hooks, and custom renderers)
- By directly using `report.st` (the Streamlit module instance) after calling `show_streamlit()`

Install extras: `pip install streamlit`

## Configure Options

```python
from pourover import Report

report = Report("Config Demo").configure_streamlit(
    page_title="PourOver — Config Demo",
    layout="wide",        # or "centered"
    height=560,            # HTML tab height
    tabs=["Report", "Markdown", "HTML", "PDF"],  # subset + order
)

report.show_streamlit()
```

## Sidebar and Lifecycle Hooks

Register callbacks that receive `(st, report)` and can emit Streamlit UI:

```python
def sidebar(st, report):
    st.header("Controls")
    st.checkbox("Show extra", key="extra")

def before(st, report):
    st.info("Rendered before tabs")

def after(st, report):
    st.success("Rendered after tabs")

report.set_streamlit_hooks(sidebar=sidebar, before_render=before, after_render=after)
report.show_streamlit()
```

## Custom Block Renderers

If you have custom block types, you can register a renderer:

```python
class MyBlock:
    def __init__(self, text: str):
        self.text = text

def render_myblock(st, block: MyBlock, report):
    st.warning(f"Custom: {block.text}")

report.register_streamlit_renderer(MyBlock, render_myblock)

sec = report.add_section("Custom")
sec.blocks.append(MyBlock("Hello from a custom block"))
report.show_streamlit()
```

## Direct Access to `st`

You can still use Streamlit directly via `report.st`:

```python
report.show_streamlit()
st = report.st
with st.sidebar:
    st.write("Added after show_streamlit()")
```

Notes
- Hooks are best for predictable placement; direct `st` calls work for one‑offs.
- If a hook raises an exception, PourOver continues rendering (and logs a gentle warning in the UI).

## Streamlit Theming (CSS injection)

Use `report.set_streamlit_theme(...)` to adjust colors and fonts, or inject custom CSS.

```python
report.set_streamlit_theme(
    primary_color="#ff6a00",
    background_color="#ffffff",
    secondary_background_color="#fafafa",
    text_color="#1f2937",
    link_color="#2563eb",
    font_family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Noto Sans', sans-serif",
)
report.show_streamlit()
```

For full control, pass `css="..."` with your own `<style>` rules — PourOver injects them safely after computed rules.

---

# Dash Customization

Install extras: `pip install dash`

You can theme Dash apps by attaching external stylesheets (e.g., Bootstrap) or injecting raw CSS.

```python
from pourover import Report

r = Report("Dash Themed")

# Use Bootstrap from a CDN
r.configure_dash(external_stylesheets=[
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
])

# Add some inline CSS for the report container
r.configure_dash(css_text="""
  h1 { color: #ff6a00; }
  iframe { border-radius: 6px; }
""")

app = r.to_dash_app()
app.run_server(debug=True)
```

Tip: The advanced Dash example (examples/dash/advanced_app.py) shows a richer app with controls, tabs, and downloads; you can pair it with the `external_stylesheets` option above for better styling.
