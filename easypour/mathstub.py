"""Lightweight TeX-to-image helper used for math rendering."""

# easypour/mathstub.py (moved under easypour)
from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


def tex_to_png(formula: str, out_dir: Path, dpi: int = 220) -> Path:
    """Render mathtext strings to tightly-cropped transparent PNG files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(formula.encode("utf-8")).hexdigest()[:12]
    out_path = out_dir / f"math_{key}.png"
    if out_path.exists():
        return out_path

    fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    t = ax.text(0.5, 0.5, f"${formula}$", ha="center", va="center")
    fig.canvas.draw()
    bbox = t.get_window_extent(renderer=fig.canvas.get_renderer()).expanded(1.15, 1.15)
    # Convert bbox to inches and resize figure
    w, h = bbox.width / dpi, bbox.height / dpi
    fig.set_size_inches(w, h)
    ax.set_position([0, 0, 1, 1])
    t.set_position((0.5, 0.5))
    fig.savefig(out_path, dpi=dpi, transparent=True)
    plt.close(fig)
    return out_path
