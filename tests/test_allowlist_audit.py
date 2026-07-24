from pathlib import Path

import allowlist
from allowlist import ALLOWLISTED_TOOLS, paths_for_tool


def test_allowlisted_tools_tuple():
    assert ALLOWLISTED_TOOLS == ("claude", "codex", "cursor", "copilot")


def test_claude_paths_only_under_claude_root(tmp_path, monkeypatch):
    claude_root = tmp_path / ".claude"
    projects = claude_root / "projects" / "p"
    projects.mkdir(parents=True)
    (projects / "s.jsonl").write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_root))
    paths = allowlist.paths_for_tool("claude", home=tmp_path, env={"CLAUDE_CONFIG_DIR": str(claude_root)})
    assert paths
    for p in paths:
        assert claude_root in p.parents or p == claude_root or str(p).startswith(str(claude_root))


def test_non_allowlisted_tool_returns_empty(tmp_path):
    assert paths_for_tool("other", home=tmp_path, env={}) == []


def test_claude_paths_for_env(tmp_path, monkeypatch):
    projects = tmp_path / "projects" / "demo"
    projects.mkdir(parents=True)
    session = projects / "s.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    paths = paths_for_tool("claude", home=tmp_path, env={"CLAUDE_CONFIG_DIR": str(tmp_path)})
    assert session in paths
