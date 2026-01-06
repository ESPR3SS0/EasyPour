"""Complex example builder used in docs/tests."""

from __future__ import annotations

from easypour.core import Report, Image


def build_report(img_path: str | None = None) -> Report:
    """Produce a multi-element report with lists, code, math, and images."""
    rpt = Report("Complex Example", author="Examples")

    s1 = rpt.add_section("Summary")
    s1.add_text(
        "This example shows bullets, checkboxes, a code block, an image, and inline styling.",
        "We measure F1[^f1] and link to <u>underlined</u> docs at [site](https://example.com).",
        "The formula below is rendered via `Section.add_math()` (inline dollar syntax is not supported).",
    )
    s1.add_bullets(["Bullet one", "Bullet two", "Bullet three"])
    s1.add_checklist([("Todo item", False), ("Completed item", True)])
    s1.add_codeblock(
        """def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n""",
        language="python",
    )
    s1.add_math(
        r"F_1 = 2 \cdot \frac{precision \cdot recall}{precision + recall}", caption="F1 score"
    )

    s2 = rpt.add_section("Artifacts")
    if img_path:
        s2.add_image(
            Image(
                path=img_path,
                alt="tiny",
                caption="A tiny image",
            )
        )

    return rpt
