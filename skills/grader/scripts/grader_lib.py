from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

DEFAULT_SESSION_LIMIT = 30

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("generic_bearer", re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
]


def redact_secrets(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(out):
            out = pattern.sub("[REDACTED_SECRET]", out)
            if label not in notes:
                notes.append(label)
    return out, notes


def empty_dossier(intake_path: str) -> dict[str, Any]:
    if intake_path not in {"auto", "export", "paste"}:
        raise ValueError(f"invalid intake_path: {intake_path}")
    return {
        "sessions_found": 0,
        "sessions_graded": 0,
        "intake_path": intake_path,
        "redaction_notes": [],
        "sessions": [],
    }


def resolve_claude_root(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = env if env is not None else os.environ
    if env.get("CLAUDE_CONFIG_DIR"):
        return Path(env["CLAUDE_CONFIG_DIR"]).expanduser()
    home = home if home is not None else Path.home()
    return home / ".claude"


def discover_session_files(claude_root: Path) -> list[Path]:
    projects = claude_root / "projects"
    if not projects.is_dir():
        return []
    return sorted(projects.rglob("*.jsonl"))


def select_recent_sessions(
    paths: list[Path], limit: int = DEFAULT_SESSION_LIMIT
) -> list[Path]:
    ranked = sorted(
        paths,
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    return ranked[:limit]
