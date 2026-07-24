"""Tests for multi-host skill installation."""

from pathlib import Path

import pytest

import install_skill


@pytest.fixture
def skill_src(tmp_path: Path) -> Path:
    src = tmp_path / "grader"
    src.mkdir()
    (src / "SKILL.md").write_text("---\nname: grader\n---\n", encoding="utf-8")
    (src / "flows").mkdir()
    (src / "flows" / "grade.md").write_text("# grade\n", encoding="utf-8")
    return src


def test_detect_host_cursor(monkeypatch):
    monkeypatch.setenv("CURSOR_AGENT", "1")
    assert install_skill.detect_host() == "cursor"


def test_detect_host_claude(monkeypatch):
    monkeypatch.delenv("CURSOR_AGENT", raising=False)
    monkeypatch.setenv("CLAUDE_CODE", "1")
    assert install_skill.detect_host() == "claude"


def test_install_cursor(skill_src: Path, tmp_path: Path):
    paths = install_skill.install(skill_src, host="cursor", home=tmp_path)
    assert paths == [tmp_path / ".cursor" / "skills" / "grader"]
    assert (paths[0] / "SKILL.md").is_file()
    assert (paths[0] / "flows" / "grade.md").is_file()


def test_install_codex_writes_both_paths(skill_src: Path, tmp_path: Path):
    paths = install_skill.install(skill_src, host="codex", home=tmp_path)
    assert tmp_path / ".codex" / "skills" / "grader" in paths
    assert tmp_path / ".agents" / "skills" / "grader" in paths
    assert (tmp_path / ".agents" / "skills" / "grader" / "SKILL.md").is_file()


def test_install_replaces_existing(skill_src: Path, tmp_path: Path):
    dest = tmp_path / ".claude" / "skills" / "grader"
    dest.mkdir(parents=True)
    (dest / "old.txt").write_text("stale", encoding="utf-8")

    install_skill.install(skill_src, host="claude", home=tmp_path)

    assert not (dest / "old.txt").exists()
    assert (dest / "SKILL.md").is_file()
