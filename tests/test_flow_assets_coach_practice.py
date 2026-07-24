"""Asset tests for the v3 Coach and Practice skill flows."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COACH_FLOW = ROOT / "skills" / "grader" / "flows" / "coach.md"
PRACTICE_FLOW = ROOT / "skills" / "grader" / "flows" / "practice.md"


@pytest.fixture
def coach_text():
    return COACH_FLOW.read_text(encoding="utf-8")


@pytest.fixture
def practice_text():
    return PRACTICE_FLOW.read_text(encoding="utf-8")


def test_coach_flow_exists_and_references_teaching_layer(coach_text):
    assert COACH_FLOW.is_file()
    assert "teaching.coaching_notes" in coach_text
    assert "lesson_ref" in coach_text


def test_coach_flow_requires_in_session_grade_report(coach_text):
    assert "GradeReport" in coach_text
    assert "judge" in coach_text.lower()
    assert "finalize_grade" in coach_text


def test_coach_flow_does_not_use_v2_unlock_gate(coach_text):
    assert "coach_sessions.jsonl" not in coach_text
    assert "trends_unlock_status" not in coach_text
    assert "5/5" not in coach_text
    assert "append_coach_session" not in coach_text


def test_practice_flow_exists_and_references_recorder(practice_text):
    assert PRACTICE_FLOW.is_file()
    assert "practice_session.record" in practice_text
    assert "practice.jsonl" in practice_text


def test_practice_flow_uses_grade_finalize_then_coach(practice_text):
    assert "finalize_grade" in practice_text
    assert "coaching_notes" in practice_text or "coach" in practice_text.lower()
    assert "judge" in practice_text.lower()


def test_practice_flow_targets_weakest_dimension_or_d1(practice_text):
    assert "weakest" in practice_text.lower() or "most_frequent_failing" in practice_text
    assert "D1" in practice_text


def test_practice_flow_no_history_credit(practice_text):
    assert "no history credit" in practice_text.lower() or "no trends credit" in practice_text.lower()


def test_practice_flow_mentions_opt_in_exemplar(practice_text):
    assert "exemplar" in practice_text.lower()
    assert "opt-in" in practice_text.lower() or "opt in" in practice_text.lower()
