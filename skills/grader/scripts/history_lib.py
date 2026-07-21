from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from grader_lib import resolve_claude_root

TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS = 5


def history_dir(claude_root: Path | None = None) -> Path:
    root = claude_root if claude_root is not None else resolve_claude_root()
    return root / "skills" / "grader" / "history"


def history_path(claude_root: Path | None = None) -> Path:
    return history_dir(claude_root) / "coach_sessions.jsonl"


def is_coach_completion(record: dict[str, Any]) -> bool:
    return bool(
        record.get("completed") is True
        and record.get("live_assessment_finished") is True
        and int(record.get("coaching_drill_rounds") or 0) >= 1
    )


def append_coach_session(record: dict[str, Any], claude_root: Path | None = None) -> Path:
    path = history_path(claude_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = dict(record)
    normalized["completed"] = is_coach_completion(normalized)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return path


def load_coach_sessions(claude_root: Path | None = None) -> list[dict[str, Any]]:
    path = history_path(claude_root)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def count_completed_coach_sessions(sessions: list[dict[str, Any]]) -> int:
    return sum(1 for session in sessions if is_coach_completion(session))


def trends_unlock_status(claude_root: Path | None = None) -> dict[str, Any]:
    completed = count_completed_coach_sessions(load_coach_sessions(claude_root))
    required = TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS
    remaining = max(0, required - completed)
    return {
        "unlocked": completed >= required,
        "completed": completed,
        "required": required,
        "remaining": remaining,
    }
