from pathlib import Path

import pytest
import consent
import allowlist
from adapters import codex as codex_ad
from adapters import cursor as cursor_ad
from adapters import copilot as copilot_ad

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "skills" / "grader" / "fixtures" / "tool_history"


@pytest.fixture
def grant(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    consent.grant_consent("codex")
    consent.grant_consent("cursor")
    consent.grant_consent("copilot")


def test_codex_paths(grant, tmp_path):
    paths = allowlist.paths_for_tool("codex", home=FIXTURES)
    assert paths
    assert all(p.suffix == ".jsonl" for p in paths)


def test_codex_discover_with_consent(grant, tmp_path):
    results = codex_ad.discover(home=FIXTURES, limit=5)
    assert results
    assert all(r["source_tool"] == "codex" for r in results)
    assert all("text" in r for r in results)
    texts = {r["text"] for r in results}
    assert "codex hello" in texts
    assert "codex prompt" in texts


def test_cursor_paths(grant, tmp_path):
    paths = allowlist.paths_for_tool("cursor", home=FIXTURES)
    assert paths
    assert all(p.suffix in {".jsonl", ".json", ".txt"} for p in paths)


def test_cursor_discover_with_consent(grant, tmp_path):
    results = cursor_ad.discover(home=FIXTURES, limit=5)
    assert results
    assert all(r["source_tool"] == "cursor" for r in results)
    texts = {r["text"] for r in results}
    assert "cursor jsonl" in texts
    assert "cursor json" in texts
    assert "cursor message" in texts


def test_copilot_paths(grant, tmp_path):
    home = FIXTURES / "copilot"
    paths = allowlist.paths_for_tool("copilot", home=home)
    assert paths
    assert all(p.is_file() for p in paths)


def test_copilot_paths_skip_directories(grant, tmp_path):
    home = tmp_path / "copilot_home"
    storage = (
        home
        / "AppData"
        / "Roaming"
        / "Code"
        / "User"
        / "globalStorage"
        / "github.copilot-chat"
        / "sessions"
    )
    storage.mkdir(parents=True)
    (storage / "chat.json").write_text('{"text": "ok"}\n', encoding="utf-8")
    (storage / "chatdir").mkdir()
    paths = allowlist.paths_for_tool("copilot", home=home)
    assert paths == [storage / "chat.json"]


def test_copilot_discover_with_consent(grant, tmp_path):
    home = FIXTURES / "copilot"
    results = copilot_ad.discover(home=home, limit=5)
    assert isinstance(results, list)
    assert all(r["source_tool"] == "copilot" for r in results)


def test_copilot_discover_skips_bad_file_continues(grant, tmp_path):
    home = tmp_path / "copilot_home"
    storage = (
        home
        / "AppData"
        / "Roaming"
        / "Code"
        / "User"
        / "globalStorage"
        / "github.copilot-chat"
        / "sessions"
    )
    storage.mkdir(parents=True)
    (storage / "good-chat.json").write_text(
        '{"text": "copilot good", "timestamp": "2026-07-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    (storage / "bad-chat.json").write_text("not json at all", encoding="utf-8")
    results = copilot_ad.discover(home=home, limit=5)
    assert results
    assert {r["text"] for r in results} == {"copilot good"}
    assert copilot_ad._partial is True


def test_copilot_summary_partial_on_failure(grant, tmp_path):
    summary = copilot_ad.scan_summary([])
    assert summary.get("partial") is True


def test_scan_intake_all_tools_with_consent(grant, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    import scan_intake

    (tmp_path / ".codex" / "sessions").mkdir(parents=True)
    (tmp_path / ".codex" / "sessions" / "s.jsonl").write_text(
        '{"text": "codex scan", "timestamp": "2026-07-01T00:00:00Z"}\n', encoding="utf-8"
    )
    (tmp_path / ".cursor" / "projects" / "p" / "agent-transcripts").mkdir(parents=True)
    (tmp_path / ".cursor" / "projects" / "p" / "agent-transcripts" / "s.jsonl").write_text(
        '{"text": "cursor scan", "timestamp": "2026-07-01T00:00:00Z"}\n', encoding="utf-8"
    )

    rc = scan_intake.main(["--tools", "codex,cursor,copilot", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    import json

    summary = json.loads(out)
    assert summary["total"] >= 2
    tools = {t["tool"]: t for t in summary["tools"]}
    assert "codex" in tools
    assert "cursor" in tools


def test_scan_intake_copilot_partial_json(grant, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    import scan_intake

    storage = (
        tmp_path
        / "AppData"
        / "Roaming"
        / "Code"
        / "User"
        / "globalStorage"
        / "github.copilot-chat"
        / "sessions"
    )
    storage.mkdir(parents=True)
    (storage / "good-chat.json").write_text(
        '{"text": "copilot scan", "timestamp": "2026-07-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    (storage / "bad-chat.json").write_text("broken", encoding="utf-8")

    rc = scan_intake.main(["--tools", "copilot", "--json"])
    assert rc == 0
    import json

    summary = json.loads(capsys.readouterr().out)
    assert summary["partial"] is True
    assert summary["total"] >= 1
