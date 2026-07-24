# tests/test_score_math.py
from domain import DIMENSION_WEIGHTS, DimensionScore, NA
from score_math import finalize, band_from_percent


def _s(dim: str, level):
    return DimensionScore(dim, level, DIMENSION_WEIGHTS[dim])


def test_band_thresholds():
    assert band_from_percent(90) == "A"
    assert band_from_percent(89.9) == "B"
    assert band_from_percent(75) == "B"
    assert band_from_percent(74.9) == "C"
    assert band_from_percent(60) == "C"
    assert band_from_percent(59.9) == "D"


def test_worked_after_example_is_a():
    # Rubric after example (D8/D9 N/A omitted)
    scores = [
        _s("D1", 3), _s("D2", 3), _s("D3", 3), _s("D4", 3), _s("D5", 2),
        _s("D6", 3), _s("D7", 2), _s("D8", NA), _s("D9", NA),
        _s("D10", 3), _s("D11", 3),
    ]
    earned, possible, percent, band, caps = finalize(
        scores, disqualifier_flags=[], target_model_class="standard"
    )
    assert earned == 55
    assert possible == 60
    assert round(percent, 2) == 91.67
    assert band == "A"
    assert caps == []


def test_na_dropped_from_denominator():
    scores = [
        _s("D1", 3), _s("D2", 3), _s("D3", 3), _s("D4", 3), _s("D5", 3),
        _s("D6", 3), _s("D7", 3), _s("D8", NA), _s("D9", NA),
        _s("D10", NA), _s("D11", NA),
    ]
    earned, possible, percent, band, caps = finalize(
        scores, disqualifier_flags=[], target_model_class="standard"
    )
    assert possible == 48  # 3*(3+2+2+2+3+2+2)
    assert earned == 48
    assert percent == 100.0


def test_disqualifier_caps_to_c():
    scores = [
        _s("D1", 3), _s("D2", 3), _s("D3", 3), _s("D4", 3), _s("D5", 3),
        _s("D6", 3), _s("D7", 3), _s("D8", NA), _s("D9", NA),
        _s("D10", NA), _s("D11", NA),
    ]
    _, _, _, band, caps = finalize(
        scores,
        disqualifier_flags=["internal_contradiction"],
        target_model_class="standard",
    )
    assert band == "C"
    assert "internal_contradiction" in caps


def test_unknown_class_suppresses_mismatch_cap_and_drops_d5():
    scores = [
        _s("D1", 3), _s("D2", 3), _s("D3", 3), _s("D4", 3), _s("D5", 3),
        _s("D6", 3), _s("D7", 3), _s("D8", NA), _s("D9", NA),
        _s("D10", NA), _s("D11", NA),
    ]
    earned, possible, percent, band, caps = finalize(
        scores,
        disqualifier_flags=["wrong_model_class"],
        target_model_class="unknown",
    )
    assert earned == 39.0
    assert possible == 39.0
    assert band == "A"
    assert "wrong_model_class" not in caps


def test_unknown_class_drops_d5_from_denominator():
    # D5=3 supplied but class unknown -> D5 excluded, not capped to 1
    scores = [_s(f"D{i}", 3) for i in range(1, 8)]
    earned, possible, percent, band, caps = finalize(
        scores, disqualifier_flags=[], target_model_class="unknown"
    )
    # possible should exclude D5's 3*3=9
    core_possible = sum(3 * DIMENSION_WEIGHTS[f"D{i}"] for i in range(1, 8))
    assert possible == core_possible - 9
    assert "wrong_model_class" not in caps


def test_known_class_keeps_d5():
    scores = [_s(f"D{i}", 3) for i in range(1, 8)]
    _e, possible, _p, _b, _c = finalize(
        scores, disqualifier_flags=[], target_model_class="standard"
    )
    core_possible = sum(3 * DIMENSION_WEIGHTS[f"D{i}"] for i in range(1, 8))
    assert possible == core_possible
