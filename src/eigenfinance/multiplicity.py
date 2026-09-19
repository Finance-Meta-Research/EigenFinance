"""Simple multiplicity helpers for multi-dataset / multi-protocol scans.

These corrections are descriptive engineering aids. They do not authorize a
scientific claim by themselves; use only after protocols and datasets are frozen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AdjustedPValue:
    label: str
    raw_p: float
    adjusted_p: float
    method: str


def _validate_pvalues(pvalues: dict[str, float]) -> list[tuple[str, float]]:
    if not pvalues:
        raise ValueError("pvalues must be non-empty")
    items: list[tuple[str, float]] = []
    for label, value in pvalues.items():
        if not label.strip():
            raise ValueError("pvalue labels must be non-empty")
        raw = float(value)
        if not math.isfinite(raw):
            raise ValueError(f"pvalue for {label!r} must be finite")
        if not 0.0 <= raw <= 1.0:
            raise ValueError(f"pvalue for {label!r} must be in [0, 1]")
        items.append((label, raw))
    return items


def bonferroni(pvalues: dict[str, float]) -> tuple[AdjustedPValue, ...]:
    """Family-wise Bonferroni adjustment: min(1, m * p_i)."""
    items = _validate_pvalues(pvalues)
    count = len(items)
    return tuple(
        AdjustedPValue(
            label=label,
            raw_p=raw,
            adjusted_p=min(1.0, count * raw),
            method="bonferroni",
        )
        for label, raw in items
    )


def holm(pvalues: dict[str, float]) -> tuple[AdjustedPValue, ...]:
    """Holm step-down adjustment (stronger than uncorrected; less conservative than Bonferroni)."""
    items = _validate_pvalues(pvalues)
    ordered = sorted(items, key=lambda pair: pair[1])
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (label, raw) in enumerate(ordered, start=1):
        candidate = (count - rank + 1) * raw
        running = max(running, candidate)
        adjusted[label] = min(1.0, running)
    return tuple(
        AdjustedPValue(
            label=label,
            raw_p=raw,
            adjusted_p=adjusted[label],
            method="holm",
        )
        for label, raw in items
    )
