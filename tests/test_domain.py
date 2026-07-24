# tests/test_domain.py
import pytest
from domain import DimensionScore, DIMENSION_WEIGHTS, NA


def test_dimension_score_rejects_null_level():
    with pytest.raises(ValueError, match="level"):
        DimensionScore("D1", None, DIMENSION_WEIGHTS["D1"])  # type: ignore[arg-type]


def test_dimension_score_accepts_na():
    ds = DimensionScore("D8", NA, DIMENSION_WEIGHTS["D8"])
    assert ds.level == NA


def test_dimension_score_rejects_level_4():
    with pytest.raises(ValueError):
        DimensionScore("D1", 4, 3)


def test_weights_match_rubric():
    assert DIMENSION_WEIGHTS == {
        "D1": 3, "D2": 2, "D3": 2, "D4": 2, "D5": 3, "D6": 2, "D7": 2,
        "D8": 3, "D9": 2, "D10": 2, "D11": 2,
    }
