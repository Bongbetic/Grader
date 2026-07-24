"""Adapters for importing prompts from external tools."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import grader_lib
import redact
import sanitize


def file_mtime_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _process_learner_text(text: str) -> tuple[str, list[str]]:
    """Sanitize, redact, and truncate learner-authored prompt text."""
    cleaned, snotes = sanitize.sanitize_learner_text(text)
    cleaned, rnotes = redact.redact_text(cleaned)
    cleaned, tnotes = grader_lib.truncate_prompt(cleaned)
    notes = list(dict.fromkeys([*snotes, *rnotes, *tnotes]))
    return cleaned, notes


def _process_assistant_text(text: str) -> tuple[str, list[str]]:
    """Redact and truncate assistant-authored turn text."""
    cleaned, rnotes = redact.redact_text(text)
    cleaned, tnotes = grader_lib.truncate_prompt(cleaned)
    notes = list(dict.fromkeys([*rnotes, *tnotes]))
    return cleaned, notes


def _make_turn(
    *,
    session_id: str,
    turn_index: int,
    role: str,
    text: str,
    timestamp: str,
    model_id: str | None = None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "turn_index": turn_index,
        "role": role,
        "text": text,
        "timestamp": timestamp,
        "model_id": model_id,
    }


def _extract_text(value: Any) -> str | None:
    """Return usable text from a JSONL value."""
    if isinstance(value, str):
        text = value
    elif isinstance(value, dict):
        text = value.get("text") or value.get("prompt") or value.get("message")
    else:
        text = None
    if text is None:
        return None
    text = str(text).strip()
    return text if text else None
