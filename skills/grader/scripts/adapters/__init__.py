"""Adapters for importing prompts from external tools."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import grader_lib
import redact
import sanitize


def _process_learner_text(text: str) -> tuple[str, list[str]]:
    """Sanitize, redact, and truncate learner-authored prompt text."""
    cleaned, snotes = sanitize.sanitize_learner_text(text)
    cleaned, rnotes = redact.redact_text(cleaned)
    cleaned, tnotes = grader_lib.truncate_prompt(cleaned)
    notes = list(dict.fromkeys([*snotes, *rnotes, *tnotes]))
    return cleaned, notes


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


def _parse_jsonl_candidates(
    path: Path,
    *,
    source_tool: str,
    model_hint: str | None = None,
) -> list[dict[str, Any]]:
    """Read a JSONL-ish file and return raw prompt candidates."""
    prompts: list[dict[str, Any]] = []
    timestamps: list[str] = []
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = (
                _extract_text(event.get("text"))
                or _extract_text(event.get("prompt"))
                or _extract_text(event.get("message"))
            )
            if not text:
                continue
            cleaned, notes = _process_learner_text(text)
            if not cleaned:
                continue
            if prompts and prompts[-1]["text"] == cleaned:
                continue
            prompts.append({
                "text": cleaned,
                "timestamp": "",
                "source_tool": source_tool,
                "model_hint": model_hint,
                "_redaction_notes": notes,
            })
            ts = event.get("timestamp") or event.get("created_at") or event.get("ts")
            if ts and isinstance(ts, str):
                timestamps.append(ts)
    if not prompts:
        return []
    timestamp = timestamps[0] if timestamps else ""
    for p in prompts:
        p["timestamp"] = timestamp
    return prompts
