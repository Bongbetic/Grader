"""Seam: render_grade_markdown — finalized report dict → contracted markdown."""
from __future__ import annotations

from render_grade_md import render_grade_markdown


def _available_report(**overrides):
    base = {
        "id": "rid",
        "prompt_id": "p-42",
        "percent": 87.2,
        "band": "C",
        "band_raw": "B",
        "modifier_reason": "efficacy:user_under_specified",
        "confidence": "low",
        "caps_applied": [],
        "dimension_scores": [
            {"dimension_id": "D1", "level": 3, "weight": 3},
            {"dimension_id": "D2", "level": 2, "weight": 2},
            {"dimension_id": "D5", "level": "N/A", "weight": 3},
        ],
        "rationales": {
            "D1": "Clear objective + checkable done.",
            "D2": "Background present; motivation thin.",
            "D5": "Model class unknown — excluded from denominator.",
        },
        "efficacy": {
            "status": "available",
            "session_id": "s1",
            "prompts_per_task_mean": 3.2,
            "single_shot_rate": 0.25,
            "attributed_rework_rate": 0.5,
            "worst_task_prompt_count": 4,
            "restates": 2,
            "corrections": 1,
            "abandoned_goal": False,
        },
        "planning": {
            "status": "available",
            "session_id": "s1",
            "planned_decomposition": 1,
            "additive_feature": 0,
            "adaptive_change_with_evidence": 0,
            "scope_change_without_prior_signal": 1,
            "under_specified_initial_plan": 1,
        },
        "excerpt": "do NOT write any code, just report…",
        "classification_summary": {
            "prompt_class": "structured_dispatch",
            "task_complexity": "moderate",
            "rework_cause": "user_under_specified",
        },
    }
    base.update(overrides)
    return base


GOLDEN_AVAILABLE = """\
# Grade report · p-42

## Topbar
Craft **C** (raw B) · ~87.2% · confidence low
modifier: efficacy:user_under_specified

## Craft
excerpt: do NOT write any code, just report…
caps: none

## Efficacy
attributed rework: 50%
restates 2 · corrections 1 · prompts/task 3.2 · single_shot 0.25 · worst 4 · abandoned_goal false
attribution: 2 restates attributed to under-specified opener — not agent misread.

## Planning
- planned_decomposition: 1
- under_specified_initial_plan: 1
- scope_change_without_prior_signal: 1
- additive_feature: 0
- adaptive_change_with_evidence: 0
callouts:
- planned_decomposition ×1
- under_specified_initial_plan ×1
- scope_change_without_prior_signal ×1

## Dimensions
D1 3 · D2 2 · D5 N/A

### Rationales
**D1:** Clear objective + checkable done.
**D2:** Background present; motivation thin.
**D5:** Model class unknown — excluded from denominator.

## Security
none detected

## Coaching

### Strongest
_(empty — fill <=120 chars)_

### Weakest
_(empty — fill <=120 chars)_

### Next actions
1. _(empty — fill <=80 chars)_
2. _(empty — fill <=80 chars)_
3. _(empty — fill <=80 chars)_
"""


def test_available_axes_golden():
    assert render_grade_markdown(_available_report()) == GOLDEN_AVAILABLE



GOLDEN_UNAVAILABLE = """\
# Grade report · p-1

## Topbar
Craft **A** (raw A) · ~91.7% · confidence uncalibrated
modifier: no_change

## Craft
excerpt: _(none)_
caps: none

## Efficacy
unavailable — no session context

## Planning
unavailable — no session context

## Dimensions
D1 3

### Rationales
**D1:** ok

## Security
none detected

## Coaching

### Strongest
_(empty — fill <=120 chars)_

### Weakest
_(empty — fill <=120 chars)_

### Next actions
1. _(empty — fill <=80 chars)_
2. _(empty — fill <=80 chars)_
3. _(empty — fill <=80 chars)_
"""


def test_unavailable_axes_golden():
    report = {
        "prompt_id": "p-1",
        "percent": 91.7,
        "band": "A",
        "band_raw": "A",
        "modifier_reason": "no_change",
        "confidence": "uncalibrated",
        "caps_applied": [],
        "dimension_scores": [{"dimension_id": "D1", "level": 3, "weight": 3}],
        "rationales": {"D1": "ok"},
        "efficacy": {"status": "unavailable", "reason": "no session context"},
        "planning": {"status": "unavailable", "reason": "no session context"},
    }
    assert render_grade_markdown(report) == GOLDEN_UNAVAILABLE


def test_caps_listed_under_craft():
    md = render_grade_markdown(
        _available_report(caps_applied=["forced_cot_on_reasoning", "internal_contradiction"])
    )
    assert "caps: forced_cot_on_reasoning, internal_contradiction" in md


def test_security_hit_block():
    md = render_grade_markdown(
        _available_report(
            security={
                "status": "hit",
                "severity": "high",
                "summary": "1 secret-shaped token matched.",
                "action": "Rotate referenced credential.",
            }
        )
    )
    assert "## Security\nseverity: high\n1 secret-shaped token matched.\naction: Rotate referenced credential." in md


def test_coaching_slots_filled_and_truncated():
    strong = "S" * 150
    weak = "W" * 150
    actions = ["A" * 100, "B" * 100, "C" * 100, "D" * 100]
    md = render_grade_markdown(
        _available_report(
            slots={
                "strongest": strong,
                "weakest": {"text": weak},
                "next_actions": actions,
            }
        )
    )
    assert ("### Strongest\n" + ("S" * 120) + "\n") in md
    assert ("### Weakest\n" + ("W" * 120) + "\n") in md
    assert "1. " + ("A" * 80) in md
    assert "2. " + ("B" * 80) in md
    assert "3. " + ("C" * 80) in md
    assert "D" * 80 not in md
    assert len([ln for ln in md.splitlines() if ln.startswith(("1. ", "2. ", "3. "))]) == 3


def test_cli_renders_report_json(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path as P

    root = P(__file__).resolve().parents[1]
    cli = root / "skills" / "grader" / "scripts" / "render_grade_md.py"
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_available_report()), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(cli), "--report", str(report_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == GOLDEN_AVAILABLE


def test_agent_misread_attribution():
    md = render_grade_markdown(
        _available_report(
            classification_summary={
                "prompt_class": "standalone",
                "task_complexity": "simple",
                "rework_cause": "agent_misread",
            }
        )
    )
    assert "attribution: 2 restates — agent misread, not your prompt." in md
