---
title: "Sample IEEE Paper"
author: "A. Researcher, B. Scientist"
date: 2026-01-06
---

# Sample IEEE Paper

**Author:** A. Researcher, B. Scientist

*2026-01-06*

## Table of Contents

- [Abstract](#abstract)
- [I. Introduction](#i-introduction)
- [II. Methodology](#ii-methodology)
- [III. Results](#iii-results)
- [References](#references)

## Abstract
<a id='abstract'></a>

This sample demonstrates EasyPour's two-column PDF capabilities. It includes figures, tables, references, and citations.

## I. Introduction
<a id='i-introduction'></a>

Edge accelerators continue to evolve [1], requiring robust reporting tools that keep up with publication-quality layouts.

## II. Methodology
<a id='ii-methodology'></a>

We generate Markdown first, then convert it to a structured PDF using EasyPour's `Report.write_pdf()` and `IEEETemplate`.

<figure style="width:70%;">![](/home/brew/ghPackages/EasyPour/examples/assets/layer_sparsity.png)<figcaption>Latency trend for the proposed system.</figcaption></figure>

**Figure 1:** Latency trend for the proposed system.

## III. Results
<a id='iii-results'></a>

| Metric | Value |
| --- | --- |
| Accuracy | 93.1% |
| F1 | 91.8% |
| Throughput (req/s) | 1.2k |


*Table 1:* Evaluation metrics on the EdgeBench dataset.

Metrics outperform the baseline reported in [2] by 7%.

## References
<a id='references'></a>

[1] J. Smith and R. Jones, "Neural Widgets," IEEE Trans., 2019.

[2] P. Nguyen, "Accelerating Edge Models," Proc. IEEE, 2021.
