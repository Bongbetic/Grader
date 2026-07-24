"""Judge-vs-human agreement per dimension."""
from __future__ import annotations

from agreement import quadratic_weighted_kappa

_DIMS = tuple(f"D{i}" for i in range(1, 12))


def dimension_agreement(gold: list[dict], judge_levels: dict[str, dict]) -> dict[str, float]:
    result: dict[str, float] = {}
    for dim in _DIMS:
        pairs_a: list[int] = []
        pairs_b: list[int] = []
        for row in gold:
            h = row["human_levels"].get(dim)
            j = judge_levels.get(row["id"], {}).get(dim)
            if isinstance(h, int) and isinstance(j, int):
                pairs_a.append(h)
                pairs_b.append(j)
        if pairs_a:
            result[dim] = quadratic_weighted_kappa(pairs_a, pairs_b)
    if result:
        result["_mean"] = sum(result.values()) / len(result)
    return result
