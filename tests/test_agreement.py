import pytest
from agreement import quadratic_weighted_kappa


def test_perfect_agreement_is_one():
    a = [0, 1, 2, 3, 2, 1]
    assert quadratic_weighted_kappa(a, a) == pytest.approx(1.0)


def test_disagreement_lowers_kappa():
    a = [0, 0, 3, 3]
    b = [3, 3, 0, 0]
    assert quadratic_weighted_kappa(a, b) < 0.0


def test_near_agreement_high_kappa():
    a = [0, 1, 2, 3, 3, 2, 1, 0]
    b = [0, 1, 2, 3, 2, 2, 1, 0]
    assert quadratic_weighted_kappa(a, b) > 0.8
