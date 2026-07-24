"""Allowlist for intake tool paths.

Only allowlisted tool trees are permitted. No arbitrary walk outside those trees.
"""
from __future__ import annotations

import glob
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import grader_lib


ALLOWLISTED_TOOLS = ("claude", "codex", "cursor", "copilot")

COPILOT_GLOB_LIMIT = 1000


def paths_for_tool(
    tool: str,
    *,
    home: Path | None = None,
    env: Mapping | None = None,
) -> list[Path]:
    """Return allowlisted file paths for ``tool``."""
    if tool not in ALLOWLISTED_TOOLS:
        return []
    if home is None:
        home = Path.home()
    env = env if env is not None else os.environ

    if tool == "claude":
        claude_root = grader_lib.resolve_claude_root(env=env, home=home)
        return grader_lib.discover_session_files(claude_root)

    if tool == "codex":
        codex_root = _resolve_codex_root(env=env, home=home)
        return _sorted_jsonl(codex_root / "sessions")

    if tool == "cursor":
        return _cursor_paths(home=home)

    if tool == "copilot":
        return _copilot_paths(home=home)

    return []


def _resolve_codex_root(
    env: Mapping[str, Any],
    home: Path,
) -> Path:
    if env.get("CODEX_HOME"):
        return Path(env["CODEX_HOME"]).expanduser()
    return home / ".codex"


def _cursor_paths(home: Path) -> list[Path]:
    results: list[Path] = []
    # Exported/grader-import transcripts.
    import_dir = home / ".cursor" / "grader-import"
    if import_dir.is_dir():
        results.extend(import_dir.rglob("*.jsonl"))
    # Cursor composer/agent transcripts.
    pattern = home / ".cursor" / "projects" / "**" / "agent-transcripts" / "*"
    for raw in glob.glob(str(pattern), recursive=True):
        p = Path(raw)
        if p.is_file() and p.suffix in {".jsonl", ".json", ".txt"}:
            results.append(p)
    return sorted(results)


def _copilot_paths(home: Path) -> list[Path]:
    base = home / "AppData" / "Roaming" / "Code" / "User" / "globalStorage"
    if not base.is_dir():
        return []
    matches: list[Path] = []
    for copilot_dir in base.glob("github.copilot*"):
        if not copilot_dir.is_dir():
            continue
        for match in copilot_dir.rglob("*chat*"):
            if match.is_file():
                matches.append(match)
    matches = sorted(matches)
    if len(matches) > COPILOT_GLOB_LIMIT:
        matches = matches[:COPILOT_GLOB_LIMIT]
    return matches


def _sorted_jsonl(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.rglob("*.jsonl"))
