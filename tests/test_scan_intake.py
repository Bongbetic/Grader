import json

import pytest
import consent
import normalize
import model_class
from adapters import claude as claude_ad
from adapters import import_paste
from domain import PromptRecord


def test_discover_without_consent_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    with pytest.raises(PermissionError):
        claude_ad.discover(limit=5)


def test_import_paste_from_text(tmp_path):
    candidates = import_paste.from_text("hello world", source="import")
    assert len(candidates) == 1
    assert candidates[0]["text"] == "hello world"
    assert candidates[0]["source_tool"] == "import"


def test_import_paste_sanitizes_boilerplate(tmp_path):
    raw = (
        "<manually_attached_skills>skill body</manually_attached_skills>\n"
        "<user_query>paste me</user_query>"
    )
    candidates = import_paste.from_text(raw, source="paste")
    assert candidates[0]["text"] == "paste me"


def test_model_class_reasoning_keywords():
    assert model_class.classify("o1-preview") == "reasoning"
    assert model_class.classify("o3-mini") == "reasoning"
    assert model_class.classify("codex") == "reasoning"
    assert model_class.classify("some-reasoning-model") == "reasoning"


def test_model_class_standard_when_present():
    assert model_class.classify("gpt-4") == "standard"
    assert model_class.classify("claude-sonnet") == "standard"


def test_model_class_unknown_when_missing():
    assert model_class.classify(None) == "unknown"
    assert model_class.classify("") == "unknown"


def test_normalize_to_prompt_record_redacts_and_excerpts(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    candidate = {
        "text": "secret key sk-ant-abcdefghijklmnopqrstuvwxyz123456",
        "timestamp": "2026-07-01T00:00:00Z",
        "source_tool": "claude",
        "model_hint": "o1",
    }
    record = normalize.to_prompt_record(candidate)
    assert isinstance(record, PromptRecord)
    assert "sk-ant-" not in record.redacted_excerpt
    assert "[REDACTED_SECRET]" in record.redacted_excerpt
    assert len(record.redacted_excerpt) <= 240
    assert record.target_model_class == "reasoning"
    assert record.redaction_flags
    assert record.persist_raw is False


def test_normalize_persist_raw(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    candidate = {
        "text": "secret key sk-ant-abcdefghijklmnopqrstuvwxyz123456",
        "timestamp": "",
        "source_tool": "paste",
        "model_hint": None,
    }
    record = normalize.to_prompt_record(candidate, persist_raw=True)
    assert record.persist_raw is True
    assert record.prompt_text is not None
    assert "sk-ant-" not in record.prompt_text
    assert "[REDACTED_SECRET]" in record.prompt_text
    assert record.redacted_text == record.prompt_text
    assert "sk-ant-" not in record.redacted_excerpt
    assert "[REDACTED_SECRET]" in record.redacted_excerpt


def test_claude_discover_with_consent(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    (projects / "s.jsonl").write_text(
        json.dumps({
            "type": "user",
            "message": {"role": "user", "content": "hello"},
            "timestamp": "2026-07-01T00:00:00Z",
        }) + "\n",
        encoding="utf-8",
    )
    consent.grant_consent("claude")
    results = claude_ad.discover(limit=5)
    assert results
    for r in results:
        assert r["source_tool"] == "claude"
        assert "text" in r
        assert "timestamp" in r


def test_scan_intake_without_consent_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    import scan_intake

    rc = scan_intake.main(["--tools", "claude", "--json"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "consent_required" in err
    assert "claude" in err


def test_scan_intake_without_consent_plain_message(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    import scan_intake

    rc = scan_intake.main(["--tools", "claude"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "consent required" in err.lower()


def test_scan_summary_redaction_count(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    results = [
        {
            "text": "secret key sk-ant-abcdefghijklmnopqrstuvwxyz123456",
            "timestamp": "2026-07-01T00:00:00Z",
            "source_tool": "claude",
            "model_hint": None,
        },
        {
            "text": "plain prompt",
            "timestamp": "2026-07-02T00:00:00Z",
            "source_tool": "claude",
            "model_hint": None,
        },
    ]
    summary = claude_ad.scan_summary(results)
    tools = {t["tool"]: t for t in summary["tools"]}
    assert tools["claude"]["redaction_count"] == 1


def test_scan_summary_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    results = [
        {"text": "a", "timestamp": "2026-07-01T00:00:00Z", "source_tool": "claude", "model_hint": None},
        {"text": "b", "timestamp": "2026-07-02T00:00:00Z", "source_tool": "claude", "model_hint": None},
        {"text": "c", "timestamp": "2026-07-03T00:00:00Z", "source_tool": "import", "model_hint": None},
    ]
    summary = claude_ad.scan_summary(results)
    assert summary["total"] == 3
    assert len(summary["tools"]) == 2
    tools = {t["tool"]: t for t in summary["tools"]}
    assert tools["claude"]["count"] == 2
    assert tools["import"]["count"] == 1


def test_scan_summary_merges_intake_stats_for_empty_tool():
    intake = {
        "cursor": {
            "sessions_found": 12,
            "sessions_scanned": 10,
            "session_limit": 10,
            "prompts_discovered": 0,
            "prompts_in_scan": 0,
            "protocol_reply_excluded": 0,
        }
    }
    summary = claude_ad.scan_summary([], intake=intake)
    assert summary["total"] == 0
    assert summary["tools"][0]["tool"] == "cursor"
    assert summary["tools"][0]["sessions_found"] == 12


def test_scan_summary_merges_intake_stats():
    results = [
        {"text": "a", "timestamp": "2026-07-01T00:00:00Z", "source_tool": "cursor", "model_hint": None},
    ]
    intake = {
        "cursor": {
            "sessions_found": 12,
            "sessions_scanned": 10,
            "session_limit": 10,
            "prompts_discovered": 539,
            "prompts_in_scan": 272,
            "protocol_reply_excluded": 3,
        }
    }
    summary = claude_ad.scan_summary(results, intake=intake)
    tools = {t["tool"]: t for t in summary["tools"]}
    assert tools["cursor"]["sessions_found"] == 12
    assert tools["cursor"]["sessions_scanned"] == 10
    assert tools["cursor"]["session_limit"] == 10
    assert tools["cursor"]["prompts_discovered"] == 539
    assert tools["cursor"]["prompts_in_scan"] == 272
    assert tools["cursor"]["protocol_reply_excluded"] == 3


def test_claude_intake_stats_reports_limit_vs_corpus(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    for idx in range(3):
        (projects / f"s{idx}.jsonl").write_text(
            json.dumps({
                "type": "user",
                "message": {"role": "user", "content": f"prompt {idx}"},
                "timestamp": "2026-07-01T00:00:00Z",
            }) + "\n",
            encoding="utf-8",
        )
    consent.grant_consent("claude")
    stats = claude_ad.intake_stats(limit=2)
    assert stats["sessions_found"] == 3
    assert stats["sessions_scanned"] == 2
    assert stats["session_limit"] == 2
    assert stats["prompts_discovered"] == 3
    assert stats["prompts_in_scan"] == 2


def test_scan_intake_json_includes_intake_stats(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    for idx in range(3):
        (projects / f"s{idx}.jsonl").write_text(
            json.dumps({
                "type": "user",
                "message": {"role": "user", "content": f"prompt {idx}"},
                "timestamp": "2026-07-01T00:00:00Z",
            }) + "\n",
            encoding="utf-8",
        )
    consent.grant_consent("claude")
    import scan_intake

    rc = scan_intake.main(["--tools", "claude", "--json", "--limit", "2"])
    assert rc == 0
    summary = json.loads(capsys.readouterr().out)
    tools = {t["tool"]: t for t in summary["tools"]}
    assert tools["claude"]["sessions_found"] == 3
    assert tools["claude"]["sessions_scanned"] == 2
    assert tools["claude"]["prompts_discovered"] == 3


def test_discover_excludes_workflow_protocol_reply(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    (projects / "s.jsonl").write_text(
        "\n".join(
            json.dumps({
                "type": "user",
                "message": {"role": "user", "content": content},
                "timestamp": "2026-07-01T00:00:00Z",
            })
            for content in ("approved", "build the login page")
        ) + "\n",
        encoding="utf-8",
    )
    consent.grant_consent("claude")
    results = claude_ad.discover(limit=5)
    assert len(results) == 1
    assert results[0]["text"] == "build the login page"
