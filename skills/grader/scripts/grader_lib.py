from __future__ import annotations

import re
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
