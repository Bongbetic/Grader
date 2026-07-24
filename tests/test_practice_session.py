from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from curriculum import list_exemplars
from domain import DIMENSION_WEIGHTS, DimensionScore, GradeReport, NA
from practice_session import pick_practice_dimension, record


def _score(dim, level):
    return DimensionScore(dim, level, DIMENSION_WEIGHTS[dim])


def _grade_report():
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
    return GradeReport(
        id="g1",
        prompt_id="p1",
        dimension_scores=scores,
        earned=42,
        possible=48,
        percent=87.5,
        band="B",
        caps_applied=[],
    )


def test_record_appends_practice_session_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    session = {
        "id": "ps-1",
        "prompt_id": "p1",
        "dimension_id": "D1",
        "learner_prompt": "Write a function.",
        "grade_report": _grade_report(),
        "coaching_notes": [{"dimension_id": "D1", "fix_text": "add acceptance test"}],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    path = record(session)
    assert path == tmp_path / "practice.jsonl"
    assert path.is_file()
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(lines) == 1
    assert lines[0]["id"] == "ps-1"
    assert lines[0]["dimension_id"] == "D1"
    assert "grade_report" in lines[0]


def test_record_without_exemplar_does_not_touch_auto_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    session = {
        "id": "ps-2",
        "prompt_id": "p2",
        "dimension_id": "D1",
        "learner_prompt": "Hello",
        "grade_report": _grade_report(),
        "coaching_notes": [],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    record(session)
    auto_dir = Path(__file__).resolve().parents[1] / "skills" / "grader" / "curriculum" / "exemplars" / "auto"
    assert not auto_dir.exists() or not list(auto_dir.glob("*.json"))


def test_record_with_exemplar_ignored_without_opt_in(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    auto_dir = Path(__file__).resolve().parents[1] / "skills" / "grader" / "curriculum" / "exemplars" / "auto"
    for leftover in auto_dir.glob("auto-d1-ignored.json"):
        leftover.unlink()

    session = {
        "id": "ps-3",
        "prompt_id": "p3",
        "dimension_id": "D1",
        "learner_prompt": "Hello",
        "grade_report": _grade_report(),
        "coaching_notes": [],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "exemplar": {"id": "auto-d1-ignored", "dimension": "D1", "before": "x", "after": "y"},
    }
    record(session)
    assert not (auto_dir / "auto-d1-ignored.json").exists()


def test_record_with_exemplar_writes_auto_when_opt_in(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    auto_dir = Path(__file__).resolve().parents[1] / "skills" / "grader" / "curriculum" / "exemplars" / "auto"
    for leftover in auto_dir.glob("auto-d1-optin.json"):
        leftover.unlink()

    config = {"auto_exemplar_opt_in": True}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    session = {
        "id": "ps-4",
        "prompt_id": "p4",
        "dimension_id": "D1",
        "learner_prompt": "Hello",
        "grade_report": _grade_report(),
        "coaching_notes": [],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "exemplar": {"id": "auto-d1-optin", "dimension": "D1", "before": "x", "after": "y"},
    }
    record(session)
    written = auto_dir / "auto-d1-optin.json"
    assert written.is_file()
    data = json.loads(written.read_text(encoding="utf-8"))
    assert data["origin"] == "auto-built"
    assert data["dimension"] == "D1"
    assert data["after"] == "y"

    # auto exemplar appears in list_exemplars
    assert any(e["id"] == "auto-d1-optin" for e in list_exemplars())

    # cleanup
    written.unlink()


def test_record_missing_required_field_raises():
    with pytest.raises(ValueError, match="id"):
        record({"prompt_id": "p1"})


def test_pick_practice_dimension_defaults_to_d1_when_trends_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    assert pick_practice_dimension() == "D1"


def test_recorded_at_added_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    session = {
        "id": "ps-5",
        "prompt_id": "p5",
        "dimension_id": "D1",
        "learner_prompt": "Hi",
        "grade_report": _grade_report(),
        "coaching_notes": [],
    }
    record(session)
    line = json.loads((tmp_path / "practice.jsonl").read_text(encoding="utf-8").strip().splitlines()[0])
    assert "recorded_at" in line
