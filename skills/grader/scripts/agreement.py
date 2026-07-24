"""Inter-rater agreement metrics (pure stdlib)."""
from __future__ import annotations


def quadratic_weighted_kappa(
    rater_a: list[int], rater_b: list[int], *, min_rating: int = 0, max_rating: int = 3
) -> float:
    if len(rater_a) != len(rater_b) or not rater_a:
        raise ValueError("raters must be equal-length and non-empty")
    n = max_rating - min_rating + 1

    def idx(r: int) -> int:
        return r - min_rating

    observed = [[0.0] * n for _ in range(n)]
    for a, b in zip(rater_a, rater_b):
        observed[idx(a)][idx(b)] += 1

    hist_a = [0.0] * n
    hist_b = [0.0] * n
    for a, b in zip(rater_a, rater_b):
        hist_a[idx(a)] += 1
        hist_b[idx(b)] += 1

    total = float(len(rater_a))
    weights = [[((i - j) ** 2) / ((n - 1) ** 2) for j in range(n)] for i in range(n)]
    expected = [[hist_a[i] * hist_b[j] / total for j in range(n)] for i in range(n)]

    num = sum(weights[i][j] * observed[i][j] for i in range(n) for j in range(n))
    den = sum(weights[i][j] * expected[i][j] for i in range(n) for j in range(n))
    if den == 0:
        return 1.0
    return 1.0 - num / den
