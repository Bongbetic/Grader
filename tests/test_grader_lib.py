import json
from pathlib import Path

import grader_lib
from grader_lib import (
    MAX_PROMPT_CHARS,
    build_dossier_from_claude_root,
    build_dossier_from_export,
    compute_signals,
    discover_session_files,
    parse_session_jsonl,
    redact_secrets,
    resolve_claude_root,
    select_recent_sessions,
    truncate_prompt,
)

FIXTURES = Path(__file__).resolve().parents[1] / "skills" / "grader" / "fixtures" / "sessions"


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


def test_default_prompt_limit_is_100():
    assert grader_lib.DEFAULT_PROMPT_LIMIT == 100


def test_default_session_limit_is_100():
    assert grader_lib.DEFAULT_SESSION_LIMIT == 100


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


def test_compute_signals_detects_correction_and_restate():
    prompts = [
        "Add a login form with email and password",
        "Add a login form with email and password fields",
        "No, wrong — use magic link auth instead",
    ]
    s = compute_signals(prompts)
    assert s["restates"] >= 1
    assert s["corrections"] >= 1


def test_parse_weak_session_extracts_user_prompts_only():
    session = parse_session_jsonl(FIXTURES / "weak_vague.jsonl")
    assert session["session_id"] == "weak1"
    assert session["user_prompts"] == ["fix it", "the bug"]
    assert session["prompt_count"] == 2
    assert session["started_at"].startswith("2026-07-01")


def test_build_dossier_from_export_weak():
    text = (
        Path(__file__).resolve().parents[1]
        / "skills/grader/fixtures/exports/weak_export.md"
    ).read_text(encoding="utf-8")
    d = build_dossier_from_export(text, intake_path="export")
    assert d["intake_path"] == "export"
    assert d["sessions_graded"] == 1
    assert d["sessions"][0]["user_prompts"] == ["fix it", "the bug"]


def test_truncate_prompt_leaves_short_text():
    text = "short prompt"
    out, notes = truncate_prompt(text)
    assert out == text
    assert notes == []


def test_truncate_prompt_caps_long_text():
    text = "x" * (MAX_PROMPT_CHARS + 500)
    out, notes = truncate_prompt(text)
    assert out.endswith(" …[truncated]")
    assert len(out) == MAX_PROMPT_CHARS + len(" …[truncated]")
    assert out[:MAX_PROMPT_CHARS] == "x" * MAX_PROMPT_CHARS
    assert notes == ["truncated_prompt"]


def test_parse_session_truncates_oversized_prompt(tmp_path):
    long_body = "a" * (MAX_PROMPT_CHARS + 100)
    path = tmp_path / "big.jsonl"
    path.write_text(
        json.dumps({
            "type": "user",
            "message": {"role": "user", "content": long_body},
            "timestamp": "2026-07-01T00:00:00Z",
        }) + "\n",
        encoding="utf-8",
    )
    session = parse_session_jsonl(path)
    assert session["prompt_count"] == 1
    assert session["user_prompts"][0].endswith(" …[truncated]")
    assert "truncated_prompt" in session["_redaction_notes"]


def test_build_dossier_from_export_truncates_oversized_prompt():
    long_body = "b" * (MAX_PROMPT_CHARS + 100)
    text = f"## session export-1\n\nuser: {long_body}\n"
    d = build_dossier_from_export(text)
    assert d["sessions_graded"] == 1
    assert d["sessions"][0]["user_prompts"][0].endswith(" …[truncated]")
    assert "truncated_prompt" in d["redaction_notes"]


def test_build_dossier_skips_empty_sessions(tmp_path):
    projects = tmp_path / "projects" / "demo"
    projects.mkdir(parents=True)
    empty = projects / "empty.jsonl"
    empty.write_text(
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "hi"}}) + "\n",
        encoding="utf-8",
    )
    nonempty = projects / "weak.jsonl"
    src = FIXTURES / "weak_vague.jsonl"
    nonempty.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    d = build_dossier_from_claude_root(tmp_path, session_limit=30)
    assert d["sessions_found"] == 2
    assert d["sessions_graded"] == 1
    assert len(d["sessions"]) == 1
    assert d["sessions"][0]["prompt_count"] == 2


def test_build_dossier_stops_at_prompt_limit(tmp_path):
    projects = tmp_path / "projects" / "demo"
    projects.mkdir(parents=True)
    # Two sessions, 3 prompts each; prompt_limit=4 -> first session full + 1 from second (newest-first)
    newer = projects / "newer.jsonl"
    older = projects / "older.jsonl"

    def write_session(path, sid, prompts, mtime_offset):
        lines = []
        for i, p in enumerate(prompts):
            lines.append(json.dumps({
                "type": "user",
                "sessionId": sid,
                "message": {"role": "user", "content": p},
                "timestamp": f"2026-07-0{i+1}T00:00:00Z",
            }))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        import os, time
        os.utime(path, (time.time() - mtime_offset, time.time() - mtime_offset))

    write_session(newer, "new", ["n1", "n2", "n3"], 0)
    write_session(older, "old", ["o1", "o2", "o3"], 100)
    d = build_dossier_from_claude_root(tmp_path, session_limit=10, prompt_limit=4)
    assert d["prompts_sampled"] == 4
    assert d["prompts_available"] == 6
    assert d["sessions_scanned"] == 2
    assert sum(s["prompt_count"] for s in d["sessions"]) == 4
    assert d["sessions"][0]["session_id"] == "new"
    assert d["sessions"][0]["user_prompts"] == ["n1", "n2", "n3"]
    assert d["sessions"][1]["user_prompts"] == ["o1"]


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
