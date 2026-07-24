"""Seam: compose_session_rollup — many finalized reports → shared-schema rollup."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from compose_session_rollup import compose_session_rollup
from render_grade_md import render_grade_markdown


def _report(
    prompt_id: str,
    *,
    percent: float,
    band: str,
    band_raw: str | None = None,
    confidence: str = "medium",
    caps: list[str] | None = None,
    dims: dict[str, int | str] | None = None,
    efficacy: dict | None = None,
    planning: dict | None = None,
    security: dict | None = None,
    slots: dict | None = None,
    excerpt: str = "sample excerpt",
    classification: dict | None = None,
    modifier_reason: str = "no_change",
    source_tool: str | None = None,
) -> dict:
    dim_map = dims or {"D1": 3, "D2": 2, "D5": "N/A"}
    dimension_scores = [
        {
            "dimension_id": dim,
            "level": level,
            "weight": {"D1": 3, "D2": 2, "D5": 3}.get(dim, 2),
        }
        for dim, level in dim_map.items()
    ]
    out: dict = {
        "id": f"rid-{prompt_id}",
        "prompt_id": prompt_id,
        "percent": percent,
        "band": band,
        "band_raw": band_raw or band,
        "modifier_reason": modifier_reason,
        "confidence": confidence,
        "caps_applied": caps or [],
        "dimension_scores": dimension_scores,
        "rationales": {
            s["dimension_id"]: f"rationale {s['dimension_id']}"
            for s in dimension_scores
        },
        "excerpt": excerpt,
        "efficacy": efficacy
        or {"status": "unavailable", "reason": "no session context"},
        "planning": planning
        or {"status": "unavailable", "reason": "no session context"},
    }
    if security is not None:
        out["security"] = security
    if slots is not None:
        out["slots"] = slots
    if classification is not None:
        out["classification_summary"] = classification
    if source_tool is not None:
        out["source_tool"] = source_tool
    return out


def test_empty_reports_raises():
    with pytest.raises(ValueError, match="at least one"):
        compose_session_rollup([])


def test_two_prompt_rollup_aggregates_core_fields():
    reports = [
        _report(
            "p-hi",
            percent=90.0,
            band="A",
            band_raw="A",
            confidence="high",
            dims={"D1": 3, "D2": 3, "D5": 2},
            efficacy={
                "status": "available",
                "session_id": "s1",
                "prompts_per_task_mean": 2.0,
                "single_shot_rate": 0.5,
                "attributed_rework_rate": 0.2,
                "worst_task_prompt_count": 3,
                "restates": 1,
                "corrections": 0,
                "abandoned_goal": False,
            },
            planning={
                "status": "available",
                "session_id": "s1",
                "planned_decomposition": 1,
                "under_specified_initial_plan": 0,
                "scope_change_without_prior_signal": 0,
                "additive_feature": 1,
                "adaptive_change_with_evidence": 0,
            },
            slots={"strongest": "clear acceptance checks"},
            classification={
                "prompt_class": "structured_dispatch",
                "task_complexity": "moderate",
                "rework_cause": "agent_misread",
            },
            source_tool="claude",
        ),
        _report(
            "p-lo",
            percent=60.0,
            band="C",
            band_raw="B",
            confidence="low",
            caps=["internal_contradiction"],
            dims={"D1": 1, "D2": 1, "D5": "N/A"},
            efficacy={
                "status": "available",
                "session_id": "s1",
                "prompts_per_task_mean": 4.0,
                "single_shot_rate": 0.0,
                "attributed_rework_rate": 0.6,
                "worst_task_prompt_count": 5,
                "restates": 2,
                "corrections": 1,
                "abandoned_goal": True,
            },
            planning={
                "status": "available",
                "session_id": "s1",
                "planned_decomposition": 0,
                "under_specified_initial_plan": 1,
                "scope_change_without_prior_signal": 1,
                "additive_feature": 0,
                "adaptive_change_with_evidence": 0,
            },
            security={
                "status": "hit",
                "severity": "high",
                "summary": "token leak",
                "action": "Rotate key",
            },
            slots={"weakest": "vague opener"},
            classification={
                "prompt_class": "vague_ask",
                "task_complexity": "simple",
                "rework_cause": "user_under_specified",
            },
            source_tool="claude",
            modifier_reason="efficacy:user_under_specified",
        ),
    ]
    rollup = compose_session_rollup(
        reports,
        intake={
            "tools": ["claude"],
            "intake_path": "auto",
            "window_start": "2026-07-01",
            "window_end": "2026-07-02",
        },
        session_id="sess-1",
    )

    assert rollup["grain"] == "session_rollup"
    assert rollup["prompt_id"] == "sess-1"
    assert rollup["percent"] == 75.0
    assert rollup["band"] == "B"
    assert rollup["band_raw"] == "A"  # modal of A,B
    assert rollup["confidence"] == "low"
    assert rollup["caps_applied"] == ["internal_contradiction"]
    assert rollup["excerpt"] == (
        "bands A×1 · C×1; classes structured_dispatch×1 · vague_ask×1"
    )
    assert rollup["intake"]["prompt_count"] == 2
    assert rollup["intake"]["tools"] == ["claude"]
    assert rollup["intake"]["intake_path"] == "auto"
    assert rollup["member_prompt_ids"] == ["p-hi", "p-lo"]

    eff = rollup["efficacy"]
    assert eff["status"] == "available"
    assert eff["restates"] == 3
    assert eff["corrections"] == 1
    assert eff["worst_task_prompt_count"] == 5
    assert eff["abandoned_goal"] is True
    assert eff["attributed_rework_rate"] == 0.4
    assert eff["prompts_per_task_mean"] == 3.0
    assert eff["single_shot_rate"] == 0.2

    plan = rollup["planning"]
    assert plan["planned_decomposition"] == 1
    assert plan["under_specified_initial_plan"] == 1
    assert plan["scope_change_without_prior_signal"] == 1
    assert plan["additive_feature"] == 1

    assert rollup["security"]["status"] == "hit"
    assert rollup["security"]["severity"] == "high"
    assert "1 of 2 prompts" in rollup["security"]["summary"]

    assert rollup["slots"]["strongest"].startswith("p-hi:")
    assert "clear acceptance" in rollup["slots"]["strongest"]
    assert rollup["slots"]["weakest"].startswith("p-lo:")
    assert "vague opener" in rollup["slots"]["weakest"]
    assert rollup["slots"]["next_actions"] == []

    d1 = next(s for s in rollup["dimension_scores"] if s["dimension_id"] == "D1")
    d5 = next(s for s in rollup["dimension_scores"] if s["dimension_id"] == "D5")
    assert d1["level"] == 2  # mean of 3 and 1
    assert d5["level"] == 2  # only one numeric (2); N/A ignored

    assert rollup["classification_summary"]["rework_cause"] in {
        "agent_misread",
        "user_under_specified",
    }


def test_three_prompt_security_and_unavailable_axes():
    reports = [
        _report("a", percent=80.0, band="B", confidence="medium"),
        _report(
            "b",
            percent=70.0,
            band="C",
            confidence="medium",
            security={
                "status": "hit",
                "severity": "low",
                "summary": "mild",
                "action": "Review",
            },
        ),
        _report(
            "c",
            percent=95.0,
            band="A",
            confidence="uncalibrated",
            security={
                "status": "hit",
                "severity": "critical",
                "summary": "jwt",
                "action": "Rotate JWT",
            },
        ),
    ]
    rollup = compose_session_rollup(reports, session_id="sess-3")
    assert rollup["percent"] == 81.7
    assert rollup["band"] == "B"
    assert rollup["confidence"] == "uncalibrated"
    assert rollup["efficacy"]["status"] == "unavailable"
    assert rollup["planning"]["status"] == "unavailable"
    assert rollup["security"]["severity"] == "critical"
    assert "2 of 3 prompts" in rollup["security"]["summary"]
    assert rollup["slots"]["strongest"].startswith("c:")
    assert rollup["slots"]["weakest"].startswith("b:")
    assert rollup["excerpt"] == "bands A×1 · B×1 · C×1"


def test_rollup_renders_markdown_intake_strip():
    reports = [
        _report("p1", percent=90.0, band="A", source_tool="cursor"),
        _report("p2", percent=70.0, band="C", source_tool="cursor"),
    ]
    rollup = compose_session_rollup(
        reports,
        intake={"intake_path": "export", "tools": ["cursor"]},
        session_id="roll-md",
    )
    md = render_grade_markdown(rollup)
    assert md.startswith("# Session rollup · roll-md\n")
    assert "intake: 2 prompts · tools=cursor · path=export" in md
    assert "behavior mix:" in md
    assert "## Topbar" in md
    assert "## Coaching" in md


def test_cli_composes_json(tmp_path: Path):
    r1 = tmp_path / "a.json"
    r2 = tmp_path / "b.json"
    r1.write_text(
        json.dumps(_report("p1", percent=90.0, band="A")), encoding="utf-8"
    )
    r2.write_text(
        json.dumps(_report("p2", percent=70.0, band="C")), encoding="utf-8"
    )
    cli = (
        Path(__file__).resolve().parents[1]
        / "skills"
        / "grader"
        / "scripts"
        / "compose_session_rollup.py"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--reports",
            str(r1),
            str(r2),
            "--session-id",
            "cli-sess",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    assert data["grain"] == "session_rollup"
    assert data["prompt_id"] == "cli-sess"
    assert data["member_prompt_ids"] == ["p1", "p2"]
