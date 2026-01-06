---
title: "Complex Example"
author: "Examples"
date: 2026-01-06
---

# Complex Example

**Author:** Examples

*2026-01-06*

## Table of Contents

- [Summary](#summary)
- [Artifacts](#artifacts)

## Summary
<a id='summary'></a>

This example shows bullets, checkboxes, a code block, an image, and inline styling.

We measure F1[^f1] and link to <u>underlined</u> docs at [site](https://example.com).

The formula below is rendered via `Section.add_math()` (inline dollar syntax is not supported).

- Bullet one
- Bullet two
- Bullet three

- [ ] Todo item
- [x] Completed item

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

```

<figure>![F_1 = 2 \cdot \frac{precision \cdot recall}{precision + recall}](.easypour_math/math_645b6fff889b.png)<figcaption>F1 score</figcaption></figure>

## Artifacts
<a id='artifacts'></a>

<figure>![tiny](/home/brew/ghPackages/EasyPour/examples/assets/tiny.png)<figcaption>A tiny image</figcaption></figure>
