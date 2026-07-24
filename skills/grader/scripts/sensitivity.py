"""Weight/threshold sensitivity: how often does the band flip under perturbation?"""
from __future__ import annotations

from domain import DIMENSION_WEIGHTS, NA
from score_math import band_from_percent

_DIMS = tuple(f"D{i}" for i in range(1, 12))


def _band_for(levels: dict, weights: dict[str, int]) -> str:
    earned = 0.0
    possible = 0.0
    for dim in _DIMS:
        level = levels.get(dim)
        if level == NA or not isinstance(level, int):
            continue
        w = weights[dim]
        earned += level * w
        possible += 3 * w
    if possible <= 0:
        return "D"
    return band_from_percent(earned / possible * 100.0)


def band_flip_rate(gold: list[dict], *, weight_overrides: dict[str, int]) -> float:
    if not gold:
        return 0.0
    weights = dict(DIMENSION_WEIGHTS)
    weights.update(weight_overrides)
    flips = 0
    for row in gold:
        base = _band_for(row["human_levels"], DIMENSION_WEIGHTS)
        perturbed = _band_for(row["human_levels"], weights)
        if base != perturbed:
            flips += 1
    return flips / len(gold)
