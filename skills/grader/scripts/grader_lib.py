from __future__ import annotations

from typing import Any

DEFAULT_SESSION_LIMIT = 30


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
