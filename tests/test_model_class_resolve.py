"""Resolve target model class when intake hint is missing (C-04 / #24)."""

from domain import DIMENSION_WEIGHTS, DimensionScore, NA
import model_class
import normalize
from score_math import finalize


def _s(dim: str, level):
    return DimensionScore(dim, level, DIMENSION_WEIGHTS[dim])


def test_resolve_prefers_model_hint_over_learner():
    assert model_class.resolve("o1-preview", learner_class="standard") == "reasoning"
    assert model_class.resolve("gpt-4o", learner_class="reasoning") == "standard"


def test_resolve_applies_learner_when_hint_missing():
    assert model_class.resolve(None, learner_class="standard") == "standard"
    assert model_class.resolve("", learner_class="reasoning") == "reasoning"


def test_resolve_stays_unknown_when_learner_skips():
    assert model_class.resolve(None, learner_class=None) == "unknown"
    assert model_class.resolve(None, learner_class="unknown") == "unknown"


def test_cursor_like_intake_learner_supplied_class_includes_d5():
    """Cursor candidates often ship model_hint=None; learner class must reach finalize."""
    candidate = {
        "text": "refactor the auth middleware to use refresh tokens",
        "timestamp": "2026-07-01T00:00:00Z",
        "source_tool": "cursor",
        "model_hint": None,
    }
    record = normalize.to_prompt_record(candidate)
    assert record.target_model_class == "unknown"

    resolved = model_class.resolve(None, learner_class="standard")
    assert resolved == "standard"

    scores = [
        _s("D1", 3),
        _s("D2", 3),
        _s("D3", 3),
        _s("D4", 3),
        _s("D5", 2),
        _s("D6", 3),
        _s("D7", 3),
        _s("D8", NA),
        _s("D9", NA),
        _s("D10", NA),
        _s("D11", NA),
    ]
    _earned, possible_unknown, _p, _b, _c = finalize(
        scores, disqualifier_flags=[], target_model_class="unknown"
    )
    _earned2, possible_resolved, _p2, _b2, _c2 = finalize(
        scores, disqualifier_flags=[], target_model_class=resolved
    )
    # D5 contributes weight × max-level to possible when class is pinned
    assert possible_resolved == possible_unknown + (3 * DIMENSION_WEIGHTS["D5"])
