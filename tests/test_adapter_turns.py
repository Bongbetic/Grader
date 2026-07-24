from pathlib import Path

import pytest
import consent
import adapters.claude as claude_adapter
import adapters.cursor as cursor_adapter
import adapters.codex as codex_adapter
from capability_matrix import capabilities_for
from turn_intake import build_turn_records

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "skills" / "grader" / "fixtures"
TOOL_FIXTURES = FIXTURES / "tool_history"


@pytest.fixture
def grant(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    consent.grant_consent("claude")
    consent.grant_consent("cursor")
    consent.grant_consent("codex")


def test_discover_turns_yields_indexed_session_turns(monkeypatch):
    fake_session = {
        "session_id": "s1",
        "started_at": "2026-07-24T00:00:00Z",
        "turns": [
            {"role": "user", "text": "first prompt", "timestamp": "2026-07-24T00:00:00Z"},
            {"role": "assistant", "text": "Sure.", "timestamp": "2026-07-24T00:00:01Z"},
            {"role": "user", "text": "second prompt", "timestamp": "2026-07-24T00:00:02Z"},
        ],
    }
    monkeypatch.setattr(claude_adapter.consent, "has_consent", lambda tool: True)
    monkeypatch.setattr(claude_adapter.allowlist, "paths_for_tool", lambda tool: ["/fake/s1.jsonl"])
    monkeypatch.setattr(
        claude_adapter.grader_lib, "select_recent_sessions", lambda paths, limit: paths
    )
    monkeypatch.setattr(
        claude_adapter.grader_lib, "parse_session_turns", lambda path: fake_session
    )

    turns = claude_adapter.discover_turns(limit=10)
    assert [t["turn_index"] for t in turns] == [0, 1, 2]
    assert [t["role"] for t in turns] == ["user", "assistant", "user"]
    assert turns[0]["session_id"] == turns[1]["session_id"] == "s1"


def test_claude_discover_turns_from_fixture(grant, monkeypatch):
    monkeypatch.setattr(
        claude_adapter.allowlist,
        "paths_for_tool",
        lambda tool: [FIXTURES / "sessions" / "weak_vague.jsonl"],
    )
    turns = claude_adapter.discover_turns(limit=5)
    roles = [t["role"] for t in turns]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 1
    assert turns[1]["text"] == "What should I fix?"


def test_cursor_discover_turns_from_fixture(grant):
    turns = cursor_adapter.discover_turns(home=TOOL_FIXTURES, limit=5)
    nested = [t for t in turns if t["session_id"] == "nested-session-uuid"]
    assert nested
    roles = [t["role"] for t in nested]
    assert "user" in roles
    assert "assistant" in roles
    assert any(t["text"] == "Working on it." for t in nested if t["role"] == "assistant")


def test_codex_discover_turns_legacy_fixture(grant):
    turns = codex_adapter.discover_turns(home=TOOL_FIXTURES, limit=5)
    legacy = [t for t in turns if t["session_id"] == "s1"]
    assert len(legacy) == 2
    assert all(t["role"] == "user" for t in legacy)
    texts = {t["text"] for t in legacy}
    assert "codex hello" in texts
    assert "codex prompt" in texts


def test_codex_discover_turns_rollout_fixture(grant):
    turns = codex_adapter.discover_turns(home=TOOL_FIXTURES, limit=5)
    rollout = [t for t in turns if t["session_id"] == "rollout-session-1"]
    assert rollout
    roles = [t["role"] for t in rollout]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 1
    assert any(t["text"] == "rollout assistant reply" for t in rollout)


def test_capability_matrix_enables_assistant_text():
    for tool in ("claude", "cursor", "codex"):
        assert capabilities_for(tool).assistant_text is True


def test_assistant_turns_survive_turn_intake(grant):
    raw = [
        {
            "session_id": "s1",
            "turn_index": 0,
            "role": "user",
            "text": "hello",
            "timestamp": "2026-07-01T00:00:00Z",
        },
        {
            "session_id": "s1",
            "turn_index": 1,
            "role": "assistant",
            "text": "Hi there.",
            "timestamp": "2026-07-01T00:00:01Z",
        },
    ]
    for tool in ("claude", "cursor", "codex"):
        recs = build_turn_records(raw, source_tool=tool, consent_covers_transcript=True)
        assert len(recs) == 2
        assert recs[1].role == "assistant"


def test_scan_summary_uses_file_mtime_fallback(tmp_path):
    results = [
        {
            "text": "no timestamp",
            "timestamp": "",
            "source_tool": "cursor",
            "model_hint": None,
            "_file_mtime": "2026-07-10T12:00:00+00:00",
        }
    ]
    summary = claude_adapter.scan_summary(results)
    tr = summary["tools"][0]["time_range"]
    assert tr["min"] == "2026-07-10T12:00:00+00:00"
    assert tr["max"] == "2026-07-10T12:00:00+00:00"
