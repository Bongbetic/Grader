from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from store import append_jsonl, save_grade
from trends import compute_trends, most_frequent_failing


def _grade_record(prompt_id: str, ingested_at: str, band: str, levels: dict[str, object]) -> dict:
    dimension_scores = [
        {"dimension_id": dim, "level": level, "weight": 2}
        for dim, level in levels.items()
    ]
    return {
        "id": f"g-{prompt_id}",
        "prompt_id": prompt_id,
        "ingested_at": ingested_at,
        "band": band,
        "dimension_scores": dimension_scores,
        "percent": 0,
        "earned": 0,
        "possible": 0,
    }


def _metric_record(ingested_at: str, band: str, levels: dict[str, int]) -> dict:
    return {
        "prompt_id": "m",
        "ingested_at": ingested_at,
        "band": band,
        "dimension_levels": levels,
    }


def _all_three_levels() -> dict[str, object]:
    return {
        "D1": 3,
        "D2": 3,
        "D3": 3,
        "D4": 3,
        "D5": 3,
        "D6": 3,
        "D7": 3,
        "D8": "N/A",
        "D9": "N/A",
        "D10": "N/A",
        "D11": "N/A",
    }


def test_insufficient_data_returns_empty_trends(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    result = compute_trends()
    assert result["available"] is False
    assert result["most_frequent_failing"] is None
    assert result["bands_over_time"] == []
    assert result["dimension_levels"] == {}
    assert result["streaks"]["consecutive_ab_bands"] == 0
    assert result["streaks"]["consecutive_practice_days"] == 0


def test_most_frequent_failing_returns_none_when_insufficient(tmp_path):
    assert most_frequent_failing(root=tmp_path) is None


def test_three_grades_yield_failing_dim_and_band_series(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    records = [
        _grade_record(
            "p1",
            (base - timedelta(hours=2)).isoformat(),
            "C",
            {**_all_three_levels(), "D1": 2, "D3": 2},
        ),
        _grade_record(
            "p2",
            (base - timedelta(hours=1)).isoformat(),
            "B",
            {**_all_three_levels(), "D1": 2},
        ),
        _grade_record(
            "p3",
            base.isoformat(),
            "A",
            _all_three_levels(),
        ),
    ]
    for i, rec in enumerate(records):
        save_grade(rec, persist_raw=False, raw_text=None, excerpt=f"ex{i}")

    result = compute_trends()
    assert result["available"] is True
    assert result["most_frequent_failing"]["dimension_id"] == "D1"
    assert result["most_frequent_failing"]["count"] == 2

    bands = [b["band"] for b in result["bands_over_time"]]
    assert bands == ["C", "B", "A"]

    assert "D1" in result["dimension_levels"]
    assert len(result["dimension_levels"]["D1"]) == 3
    d1_levels = [pt["level"] for pt in result["dimension_levels"]["D1"]]
    assert d1_levels == [2, 2, 3]


def test_metrics_covering_two_periods_unlocks_trends(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    append_jsonl(
        tmp_path / "metrics.jsonl",
        _metric_record(
            (base - timedelta(days=1)).isoformat(),
            "B",
            {"D1": 2, "D2": 3},
        ),
    )
    append_jsonl(
        tmp_path / "metrics.jsonl",
        _metric_record(
            base.isoformat(),
            "C",
            {"D1": 1, "D2": 2},
        ),
    )

    result = compute_trends()
    assert result["available"] is True
    assert result["most_frequent_failing"]["dimension_id"] == "D1"
    assert result["most_frequent_failing"]["count"] == 2


def test_streaks_count_consecutive_ab_bands(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    for i, band in enumerate(["A", "B", "A"]):
        rec = _grade_record(
            f"s{i}",
            (base - timedelta(hours=i)).isoformat(),
            band,
            _all_three_levels(),
        )
        save_grade(rec, persist_raw=False, raw_text=None, excerpt=f"e{i}")

    result = compute_trends()
    assert result["streaks"]["consecutive_ab_bands"] == 3


def test_streaks_reset_when_latest_band_not_ab(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    for i, band in enumerate(["C", "B", "A"]):
        rec = _grade_record(
            f"r{i}",
            (base - timedelta(hours=i)).isoformat(),
            band,
            _all_three_levels(),
        )
        save_grade(rec, persist_raw=False, raw_text=None, excerpt=f"e{i}")

    result = compute_trends()
    assert result["streaks"]["consecutive_ab_bands"] == 0


def test_practice_streak_counts_consecutive_days(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    for i in range(2):
        rec = _grade_record(
            f"psg{i}",
            (base - timedelta(hours=i)).isoformat(),
            "B",
            _all_three_levels(),
        )
        save_grade(rec, persist_raw=False, raw_text=None, excerpt=f"e{i}")
    for i in range(3):
        append_jsonl(
            tmp_path / "practice.jsonl",
            {
                "id": f"ps-{i}",
                "prompt_id": "p",
                "dimension_id": "D1",
                "learner_prompt": "hello",
                "grade_report": {},
                "coaching_notes": [],
                "recorded_at": (base - timedelta(days=i)).isoformat(),
            },
        )

    result = compute_trends()
    assert result["streaks"]["consecutive_practice_days"] == 3


def test_trends_report_cli_prints_json(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    base = datetime.now(timezone.utc)
    for i in range(2):
        rec = _grade_record(
            f"cli{i}",
            (base - timedelta(hours=i)).isoformat(),
            "B",
            {**_all_three_levels(), "D1": 2},
        )
        save_grade(rec, persist_raw=False, raw_text=None, excerpt=f"cli{i}")

    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "skills" / "grader" / "scripts" / "trends_report.py"),
            "--json",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["available"] is True
    assert data["most_frequent_failing"]["dimension_id"] == "D1"
