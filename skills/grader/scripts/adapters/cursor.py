"""Cursor adapter: discover user prompts from exported Cursor transcripts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import consent
import grader_lib
import allowlist
from adapters import _extract_text, _process_learner_text


def discover(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return raw prompt candidates from Cursor transcripts.

    Raises ``PermissionError`` if the user has not granted consent for Cursor.
    """
    if not consent.has_consent("cursor"):
        raise PermissionError("Cursor intake consent not granted")

    paths = allowlist.paths_for_tool("cursor", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    candidates: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix in {".jsonl", ".json"}:
            candidates.extend(_parse_cursor_jsonl(path))
        elif path.suffix == ".txt":
            candidates.extend(_parse_txt_candidates(path))
    return candidates


def _file_mtime_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _parse_cursor_jsonl(path: Path) -> list[dict[str, Any]]:
    """Parse Cursor agent-transcript JSONL (role + message.content[] shape)."""
    prompts: list[dict[str, Any]] = []
    timestamps: list[str] = []
    fallback_ts = _file_mtime_iso(path)
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue

            role = event.get("role")
            if role is not None and str(role).lower() != "user":
                continue

            text = _extract_cursor_text(event)
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
                "source_tool": "cursor",
                "model_hint": None,
                "_redaction_notes": notes,
            })
            ts = event.get("timestamp") or event.get("created_at") or event.get("ts")
            if ts and isinstance(ts, str):
                timestamps.append(ts)

    if not prompts:
        return []
    timestamp = timestamps[0] if timestamps else fallback_ts
    for prompt in prompts:
        prompt["timestamp"] = timestamp
    return prompts


def _extract_cursor_text(event: dict[str, Any]) -> str | None:
    message = event.get("message")
    if isinstance(message, dict):
        content_text = grader_lib._content_to_text(message.get("content"))
        if content_text:
            return content_text.strip() or None

    return (
        _extract_text(event.get("text"))
        or _extract_text(event.get("prompt"))
        or _extract_text(event.get("message"))
    )


def _parse_txt_candidates(path: Path) -> list[dict[str, Any]]:
    """Treat each non-empty line of a .txt transcript as a prompt."""
    candidates: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            cleaned, notes = _process_learner_text(text)
            if not cleaned:
                continue
            candidates.append({
                "text": cleaned,
                "timestamp": "",
                "source_tool": "cursor",
                "model_hint": None,
                "_redaction_notes": notes,
            })
    return candidates


def scan_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    return claude_ad.scan_summary(results)
