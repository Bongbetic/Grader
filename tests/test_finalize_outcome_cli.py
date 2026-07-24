"""CLI seam: finalize_grade outcome JSON paths + grades.jsonl flat fields."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JUDGE = ROOT / "skills" / "grader" / "fixtures" / "judge" / "valid_after.json"
CLI = ROOT / "skills" / "grader" / "scripts" / "finalize_grade.py"
FLOOR_OK = "0.7"


def _run(tmp_path, monkeypatch, extra_args: list[str]):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--judge",
            str(JUDGE),
            "--prompt-id",
            "p-out",
            "--excerpt",
            "hello",
            "--model-class",
            "standard",
            *extra_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_no_outcome_json_emits_unavailable(tmp_path, monkeypatch):
    proc = _run(tmp_path, monkeypatch, ["--mean-kappa", FLOOR_OK])
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["band_raw"] == "A"
    assert report["band"] == "A"
    assert report["modifier_reason"] == "no_change"
    assert report["efficacy"]["status"] == "unavailable"
    assert report["efficacy"]["reason"] == "no session context"
    assert report["planning"]["status"] == "unavailable"

    line = json.loads((tmp_path / "grades.jsonl").read_text(encoding="utf-8").strip())
    assert line["efficacy"]["status"] == "unavailable"
    assert line["band_raw"] == "A"


def test_cli_both_json_applies_modifier(tmp_path, monkeypatch):
    eff = tmp_path / "eff.json"
    plan = tmp_path / "plan.json"
    eff.write_text(
        json.dumps(
            {
                "session_id": "s1",
                "prompts_per_task_mean": 3.0,
                "single_shot_rate": 0.2,
                "attributed_rework_rate": 0.5,
                "worst_task_prompt_count": 4,
                "restates": 2,
                "corrections": 1,
                "abandoned_goal": False,
                "high_confidence_user_underspec": True,
            }
        ),
        encoding="utf-8",
    )
    plan.write_text(
        json.dumps(
            {
                "session_id": "s1",
                "planned_decomposition": 0,
                "additive_feature": 0,
                "adaptive_change_with_evidence": 0,
                "scope_change_without_prior_signal": 0,
                "under_specified_initial_plan": 0,
                "high_confidence_underspec": False,
            }
        ),
        encoding="utf-8",
    )
    proc = _run(
        tmp_path,
        monkeypatch,
        [
            "--mean-kappa",
            FLOOR_OK,
            "--efficacy-json",
            str(eff),
            "--planning-json",
            str(plan),
        ],
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["band_raw"] == "A"
    assert report["band"] == "B"
    assert "efficacy" in report["modifier_reason"]
    assert report["efficacy"]["status"] == "available"
    assert "high_confidence_user_underspec" not in report["efficacy"]
    assert report["planning"]["status"] == "available"

    line = json.loads((tmp_path / "grades.jsonl").read_text(encoding="utf-8").strip())
    assert line["band"] == "B"
    assert line["band_raw"] == "A"


def test_cli_bad_efficacy_json_exits_1(tmp_path, monkeypatch):
    eff = tmp_path / "eff.json"
    plan = tmp_path / "plan.json"
    eff.write_text(json.dumps({"session_id": "s1"}), encoding="utf-8")
    plan.write_text(
        json.dumps(
            {
                "session_id": "s1",
                "planned_decomposition": 0,
                "additive_feature": 0,
                "adaptive_change_with_evidence": 0,
                "scope_change_without_prior_signal": 0,
                "under_specified_initial_plan": 0,
            }
        ),
        encoding="utf-8",
    )
    proc = _run(
        tmp_path,
        monkeypatch,
        ["--efficacy-json", str(eff), "--planning-json", str(plan)],
    )
    assert proc.returncode == 1
    assert "attributed_rework_rate" in proc.stderr or "error" in proc.stderr.lower()
