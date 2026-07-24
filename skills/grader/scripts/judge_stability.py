"""Variance of judge classifications across repeated runs."""
from __future__ import annotations

from collections import Counter


def classification_stability(runs: list[dict[str, str]]) -> dict[str, float]:
    if not runs:
        return {}
    fields: set[str] = set()
    for r in runs:
        fields.update(r.keys())
    n = len(runs)
    out: dict[str, float] = {}
    for field in fields:
        values = [r[field] for r in runs if field in r]
        if not values:
            continue
        modal = Counter(values).most_common(1)[0][1]
        out[field] = modal / n
    return out
