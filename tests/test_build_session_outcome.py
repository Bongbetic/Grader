"""Seam: build_session_outcome — discover_turns → efficacy/planning JSON for finalize."""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import consent
import pytest
from build_session_outcome import (
    build_session_outcome,
    cap_follow_up_confidence,
    discover_turns_for_tool,
)
from render_grade_md import render_grade_markdown

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "skills" / "grader" / "fixtures"
TOOL_FIXTURES = FIXTURES / "tool_history"
JUDGE = FIXTURES / "judge" / "valid_after.json"
FINALIZE = ROOT / "skills" / "grader" / "scripts" / "finalize_grade.py"


@pytest.fixture
def grant(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    for tool in ("claude", "cursor", "codex"):
        consent.grant_consent(tool, root=tmp_path)
    consent.grant_transcript_consent(root=tmp_path)


def test_unsupported_tool_returns_none():
    efficacy, planning = build_session_outcome("copilot")
    assert efficacy is None
    assert planning is None


def test_cap_tool_environment_at_medium_for_cursor():
    labels = {
        (0, 1): {
            "value": "restate_unmet_intent",
            "cause": "tool_or_environment",
            "confidence": "high",
        }
    }
    capped = cap_follow_up_confidence(labels, "cursor")
    assert capped[(0, 1)]["confidence"] == "medium"


def test_cap_leaves_claude_high_confidence():
    labels = {
        (0, 1): {
            "value": "restate_unmet_intent",
            "cause": "tool_or_environment",
            "confidence": "high",
        }
    }
    capped = cap_follow_up_confidence(labels, "claude")
    assert capped[(0, 1)]["confidence"] == "high"


@pytest.mark.parametrize("tool", ("claude", "cursor", "codex"))
def test_discover_turns_dispatch_per_tool(grant, tool, monkeypatch):
    if tool == "claude":
        monkeypatch.setattr(
            "adapters.claude.allowlist.paths_for_tool",
            lambda t: [FIXTURES / "sessions" / "weak_vague.jsonl"],
        )
    turns = discover_turns_for_tool(tool, home=TOOL_FIXTURES, limit=10)
    assert turns
    assert all("session_id" in t for t in turns)
    assert any(t["role"] == "user" for t in turns)


@pytest.mark.parametrize(
    "tool,session_id",
    [
        ("claude", "weak1"),
        ("cursor", "nested-session-uuid"),
        ("codex", "rollout-session-1"),
    ],
)
def test_build_outcome_available_per_session_tool(
    grant, tool, session_id, monkeypatch
):
    if tool == "claude":
        monkeypatch.setattr(
            "adapters.claude.allowlist.paths_for_tool",
            lambda t: [FIXTURES / "sessions" / "weak_vague.jsonl"],
        )
    efficacy, planning = build_session_outcome(
        tool,
        session_id=session_id,
        home=TOOL_FIXTURES,
        consent_covers_transcript=True,
    )
    assert efficacy is not None
    assert planning is not None
    assert efficacy["session_id"] == session_id
    assert planning["session_id"] == session_id
    assert efficacy["prompts_per_task_mean"] >= 0
    assert planning["planned_decomposition"] >= 0


@pytest.mark.parametrize(
    "tool,session_id",
    [
        ("claude", "weak1"),
        ("cursor", "nested-session-uuid"),
        ("codex", "rollout-session-1"),
    ],
)
def test_tri_pane_integration_fixture_finalize_render(
    grant, tool, session_id, tmp_path, monkeypatch
):
    if tool == "claude":
        monkeypatch.setattr(
            "adapters.claude.allowlist.paths_for_tool",
            lambda t: [FIXTURES / "sessions" / "weak_vague.jsonl"],
        )
    efficacy, planning = build_session_outcome(
        tool,
        session_id=session_id,
        home=TOOL_FIXTURES,
        consent_covers_transcript=True,
    )
    assert efficacy is not None and planning is not None

    eff_path = tmp_path / "efficacy.json"
    plan_path = tmp_path / "planning.json"
    eff_path.write_text(json.dumps(efficacy), encoding="utf-8")
    plan_path.write_text(json.dumps(planning), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(FINALIZE),
            "--judge",
            str(JUDGE),
            "--prompt-id",
            f"p-{tool}",
            "--excerpt",
            "graded prompt excerpt",
            "--model-class",
            "standard",
            "--efficacy-json",
            str(eff_path),
            "--planning-json",
            str(plan_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GRADER_HOME": str(tmp_path)},
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["efficacy"]["status"] == "available"
    assert report["planning"]["status"] == "available"

    md = render_grade_markdown(report)
    assert "unavailable — no session context" not in md
    assert "## Efficacy" in md
    assert "## Planning" in md
