import grader_lib
from grader_lib import (
    discover_session_files,
    redact_secrets,
    resolve_claude_root,
    select_recent_sessions,
)


def test_redact_sk_api_key_pattern():
    raw = "use key sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789abcdefghij"
    cleaned, notes = redact_secrets(raw)
    assert "sk-ant-api03-" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned
    assert notes  # non-empty


def test_redact_leaves_normal_prompt():
    raw = "Add dark mode toggle to settings"
    cleaned, notes = redact_secrets(raw)
    assert cleaned == raw
    assert notes == []


def test_default_session_limit_is_30():
    assert grader_lib.DEFAULT_SESSION_LIMIT == 30


def test_empty_dossier_schema():
    d = grader_lib.empty_dossier("auto")
    assert d["intake_path"] == "auto"
    assert d["sessions_found"] == 0
    assert d["sessions_graded"] == 0
    assert d["sessions"] == []
    assert d["redaction_notes"] == []


def test_resolve_claude_root_uses_env(tmp_path, monkeypatch):
    custom = tmp_path / "custom-claude"
    custom.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(custom))
    assert resolve_claude_root() == custom


def test_discover_and_select_recent(tmp_path):
    projects = tmp_path / "projects"
    a = projects / "proj-a"
    b = projects / "proj-b" / "sessions"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    f1 = a / "old.jsonl"
    f2 = b / "new.jsonl"
    f1.write_text("{}\n", encoding="utf-8")
    f2.write_text("{}\n", encoding="utf-8")
    # ensure mtime ordering
    import os, time
    os.utime(f1, (time.time() - 100, time.time() - 100))
    os.utime(f2, (time.time(), time.time()))
    found = discover_session_files(tmp_path)
    assert set(found) == {f1, f2}
    recent = select_recent_sessions(found, limit=1)
    assert recent == [f2]
