from __future__ import annotations

import pytest
from curriculum import load_lesson, list_exemplars, list_lessons
from domain import DIMENSION_WEIGHTS, DimensionScore, GradeReport, NA
from teaching import TEACHING_FIXES, coaching_notes


def _score(dim, level):
    return DimensionScore(dim, level, DIMENSION_WEIGHTS[dim])


def test_teaching_fixes_cover_all_dimensions():
    for dim in DIMENSION_WEIGHTS:
        assert dim in TEACHING_FIXES
        assert TEACHING_FIXES[dim]


def test_list_lessons_has_twelve():
    lessons = list_lessons()
    assert len(lessons) == 12
    for dim in DIMENSION_WEIGHTS:
        assert dim in lessons
    assert "model-fit-meta" in lessons


def test_each_lesson_has_heading_and_try_this():
    for lesson_id in list_lessons():
        text = load_lesson(lesson_id)
        assert text.startswith("#")
        assert "try this" in text.lower() or "try:" in text.lower()


def test_load_lesson_missing_raises():
    with pytest.raises((FileNotFoundError, ValueError)):
        load_lesson("does-not-exist")


def test_list_exemplars_has_at_least_twelve_seed():
    exemplars = list_exemplars()
    assert len(exemplars) >= 12
    assert all(e.get("origin") == "seed" for e in exemplars)


def test_every_dimension_has_seed_exemplar():
    dims = {e["dimension"] for e in list_exemplars()}
    for dim in DIMENSION_WEIGHTS:
        assert dim in dims, f"missing seed exemplar for {dim}"


def test_coaching_notes_emits_fix_for_level_two_d1():
    scores = [
        _score("D1", 2),
        _score("D2", 3),
        _score("D3", 3),
        _score("D4", 3),
        _score("D5", 3),
        _score("D6", 3),
        _score("D7", 3),
        _score("D8", NA),
        _score("D9", NA),
        _score("D10", NA),
        _score("D11", NA),
    ]
    report = GradeReport(
        id="g1",
        prompt_id="p1",
        dimension_scores=scores,
        earned=42,
        possible=48,
        percent=87.5,
        band="B",
        caps_applied=[],
    )
    notes = coaching_notes(report)
    d1_notes = [n for n in notes if n["dimension_id"] == "D1"]
    assert len(d1_notes) == 1
    assert d1_notes[0]["fix_text"] == TEACHING_FIXES["D1"]
    assert d1_notes[0]["lesson_ref"] == "D1"


def test_coaching_notes_skips_na_and_perfect_scores():
    scores = [
        _score("D1", 3),
        _score("D2", NA),
        _score("D3", 1),
        _score("D4", 3),
        _score("D5", 3),
        _score("D6", 3),
        _score("D7", 3),
        _score("D8", NA),
        _score("D9", NA),
        _score("D10", NA),
        _score("D11", NA),
    ]
    report = GradeReport(
        id="g2",
        prompt_id="p2",
        dimension_scores=scores,
        earned=30,
        possible=48,
        percent=62.5,
        band="C",
        caps_applied=[],
    )
    notes = coaching_notes(report)
    assert all(n["dimension_id"] == "D3" for n in notes)
    assert len(notes) == 1
