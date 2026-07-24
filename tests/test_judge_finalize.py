import json
import subprocess
import sys
from pathlib import Path

import pytest
from domain import DIMENSION_WEIGHTS, NA, DimensionScore, GradeReport
from gold_set import load_gold
from judge_schema import build_grade_report, parse_judge_output

ROOT = Path(__file__).resolve().parents[1]
JUDGE_FIXTURES = ROOT / "skills" / "grader" / "fixtures" / "judge"
GOLD_FAIRNESS = ROOT / "skills" / "grader" / "fixtures" / "gold" / "fairness.jsonl"
VALID_JUDGE = JUDGE_FIXTURES / "valid_after.json"
INVALID_JUDGE = JUDGE_FIXTURES / "invalid_missing_d1.json"
TERSE_CONTINUATION_JUDGE = JUDGE_FIXTURES / "fair_terse_valid_continuation.json"
CLI = ROOT / "skills" / "grader" / "scripts" / "finalize_grade.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_parse_judge_output_valid_after_example():
    data = _load(VALID_JUDGE)
    scores, rationales, flags = parse_judge_output(data)
    assert len(scores) == 11
    assert all(isinstance(s, DimensionScore) for s in scores)
    assert [s.dimension_id for s in scores] == [
        "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11"
    ]
    assert scores[0] == DimensionScore("D1", 3, DIMENSION_WEIGHTS["D1"])
    assert scores[4] == DimensionScore("D5", 2, DIMENSION_WEIGHTS["D5"])
    assert scores[7].level == NA
    assert scores[8].level == NA
    assert flags == []
    assert "D1" in rationales


def test_parse_judge_output_rejects_missing_d1():
    data = _load(INVALID_JUDGE)
    with pytest.raises(ValueError, match="D1"):
        parse_judge_output(data)


def test_parse_judge_output_rejects_null_level():
    data = _load(VALID_JUDGE)
    data["dimensions"]["D1"]["level"] = None
    with pytest.raises(ValueError, match="level"):
        parse_judge_output(data)


def test_parse_judge_output_rejects_level_out_of_range():
    data = _load(VALID_JUDGE)
    data["dimensions"]["D1"]["level"] = 4
    with pytest.raises(ValueError, match="level"):
        parse_judge_output(data)


def test_parse_judge_output_rejects_unknown_dimension():
    data = _load(VALID_JUDGE)
    data["dimensions"]["D12"] = {"level": 3, "rationale": "extra"}
    with pytest.raises(ValueError, match="unknown dimensions: D12"):
        parse_judge_output(data)


def test_build_grade_report_computes_band_a_and_ignores_input_percent():
    data = _load(VALID_JUDGE)
    data["percent"] = 0
    data["band"] = "D"
    scores, rationales, flags = parse_judge_output(data)
    report = build_grade_report("p-1", scores, rationales, flags, "standard")
    assert isinstance(report, GradeReport)
    assert report.band == "A"
    assert round(report.percent, 2) == 91.67
    assert report.caps_applied == []
    assert report.prompt_id == "p-1"


def test_build_grade_report_redacts_rationales():
    data = _load(VALID_JUDGE)
    data["dimensions"]["D1"]["rationale"] = "Contact me at alice@example.com"
    scores, rationales, flags = parse_judge_output(data)
    report = build_grade_report("p-2", scores, rationales, flags, "standard")
    assert "alice@example.com" not in report.rationales["D1"]
    assert "[REDACTED_EMAIL]" in report.rationales["D1"]


def test_build_grade_report_applies_disqualifier_cap():
    data = _load(VALID_JUDGE)
    data["disqualifiers"] = ["internal_contradiction"]
    scores, rationales, flags = parse_judge_output(data)
    report = build_grade_report("p-3", scores, rationales, flags, "standard")
    assert report.band == "C"
    assert "internal_contradiction" in report.caps_applied


def test_finalize_grade_cli_writes_json_to_stdout_and_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--judge",
            str(VALID_JUDGE),
            "--prompt-id",
            "p-4",
            "--excerpt",
            "hello world",
            "--model-class",
            "standard",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["prompt_id"] == "p-4"
    assert report["band"] == "A"
    assert round(report["percent"], 2) == 91.67

    grades_path = tmp_path / "grades.jsonl"
    assert grades_path.is_file()
    line = json.loads(grades_path.read_text(encoding="utf-8").strip())
    assert line["prompt_id"] == "p-4"
    assert line["band"] == "A"

    excerpt_path = tmp_path / "excerpts" / "p-4.txt"
    assert excerpt_path.is_file()
    assert excerpt_path.read_text(encoding="utf-8") == "hello world"

    metrics_path = tmp_path / "metrics.jsonl"
    assert metrics_path.is_file()
    metric = json.loads(metrics_path.read_text(encoding="utf-8").strip())
    assert metric["prompt_id"] == "p-4"
    assert metric["band"] == "A"
    assert "hash" in metric


def test_finalize_grade_cli_persists_raw_when_requested(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    raw_path = tmp_path / "raw.txt"
    raw_path.write_text("raw prompt text", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--judge",
            str(VALID_JUDGE),
            "--prompt-id",
            "p-5",
            "--excerpt",
            "excerpt",
            "--raw",
            str(raw_path),
            "--persist-raw",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    persisted_raw = tmp_path / "raw" / "p-5.txt"
    assert persisted_raw.is_file()
    assert persisted_raw.read_text(encoding="utf-8") == "raw prompt text"
    report = json.loads(proc.stdout)
    assert report["prompt_id"] == "p-5"
    assert report["band"] == "A"


def test_finalize_grade_cli_persist_raw_redacts_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    raw_path = tmp_path / "raw.txt"
    raw_path.write_text(
        "secret key sk-ant-abcdefghijklmnopqrstuvwxyz123456\nemail me alice@example.com",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--judge",
            str(VALID_JUDGE),
            "--prompt-id",
            "p-5-redacted",
            "--excerpt",
            "excerpt",
            "--raw",
            str(raw_path),
            "--persist-raw",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    persisted_raw = tmp_path / "raw" / "p-5-redacted.txt"
    assert persisted_raw.is_file()
    stored = persisted_raw.read_text(encoding="utf-8")
    assert "sk-ant-" not in stored
    assert "alice@example.com" not in stored
    assert "[REDACTED_SECRET]" in stored
    assert "[REDACTED_EMAIL]" in stored
    report = json.loads(proc.stdout)
    assert "raw_redaction_notes" in report


def test_finalize_grade_cli_redacts_excerpt_and_exits_on_invalid_judge(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--judge",
            str(INVALID_JUDGE),
            "--prompt-id",
            "p-6",
            "--excerpt",
            "excerpt",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "D1" in proc.stderr or "missing" in proc.stderr


def test_fair_terse_valid_continuation_finalize_not_band_d():
    """Gold fixture: proportional judge scores terse git continuation near band B, not D."""
    gold = {r["id"]: r for r in load_gold(GOLD_FAIRNESS)}["fair-terse-valid-continuation"]
    data = json.loads(TERSE_CONTINUATION_JUDGE.read_text(encoding="utf-8"))

    classification = data["classification"]
    assert classification["task_complexity"]["value"] in ("trivial", "simple")
    assert classification["prompt_class"]["value"] == "valid_continuation"

    scores, rationales, flags = parse_judge_output(data)
    levels = {s.dimension_id: s.level for s in scores}
    for dim, expected in gold["human_levels"].items():
        assert levels[dim] == expected, f"{dim}: judge {levels[dim]} != gold {expected}"

    report = build_grade_report(
        "fair-terse-valid-continuation",
        scores,
        rationales,
        flags,
        gold["model_class"],
    )
    assert report.band != "D"
    assert report.band in ("B", "C")
    assert levels["D2"] == 2
