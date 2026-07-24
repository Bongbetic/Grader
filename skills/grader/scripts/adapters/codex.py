"""Codex adapter: discover user prompts from local Codex sessions.

Codex rollout JSONL (``~/.codex/sessions/**/rollout-*.jsonl``) uses one JSON
object per line with top-level ``timestamp``, ``type``, and ``payload``:

- ``response_item`` + ``payload.type == message`` — ``role`` is
  ``user``/``assistant``; ``content`` blocks use ``input_text`` or
  ``output_text``.
- ``event_msg`` + ``payload.type == user_message`` — plain-string user turn.
- ``event_msg`` + ``payload.type == agent_message`` — assistant reasoning text.
- ``session_meta`` — session id in ``payload.id``.

Legacy/simple lines (older fixtures) may use flat ``text`` or ``prompt`` fields
for user-only turns.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import consent
import grader_lib
import allowlist
from adapters import (
    _extract_text,
    _make_turn,
    _process_assistant_text,
    _process_learner_text,
    file_mtime_iso,
)


def discover(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return raw prompt candidates from Codex sessions.

    Raises ``PermissionError`` if the user has not granted consent for Codex.
    """
    if not consent.has_consent("codex"):
        raise PermissionError("Codex intake consent not granted")

    paths = allowlist.paths_for_tool("codex", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)
    candidates, _excluded = _discover_paths(paths)
    return candidates


def intake_stats(*, home: Path | None = None, limit: int = 100) -> dict[str, Any]:
    """Return session-limit vs full-corpus counts for scan summaries."""
    if not consent.has_consent("codex"):
        raise PermissionError("Codex intake consent not granted")

    paths = allowlist.paths_for_tool("codex", home=home)
    selected = grader_lib.select_recent_sessions(paths, limit=limit)
    all_candidates, corpus_excluded = _discover_paths(paths)
    scan_candidates, scan_excluded = _discover_paths(selected)
    return {
        "sessions_found": len(paths),
        "sessions_scanned": len(selected),
        "session_limit": limit,
        "prompts_discovered": len(all_candidates),
        "prompts_in_scan": len(scan_candidates),
        "protocol_reply_excluded": scan_excluded,
        "protocol_reply_excluded_corpus": corpus_excluded,
    }


def _discover_paths(paths: list[Path]) -> tuple[list[dict[str, Any]], int]:
    candidates: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
    for path in paths:
        file_candidates, excluded = _parse_codex_candidates(path)
        protocol_reply_excluded += excluded
        candidates.extend(file_candidates)
    return candidates, protocol_reply_excluded


def discover_turns(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return session-structured user and assistant turns from Codex sessions."""
    if not consent.has_consent("codex"):
        raise PermissionError("Codex intake consent not granted")

    paths = allowlist.paths_for_tool("codex", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    turns: list[dict[str, Any]] = []
    for path in paths:
        turns.extend(_parse_codex_turns(path)[0])
    return turns


def _codex_session_id(path: Path, event: dict[str, Any] | None = None) -> str:
    if event:
        payload = event.get("payload") or {}
        if event.get("type") == "session_meta" and payload.get("id"):
            return str(payload["id"])
    return path.stem


def _extract_codex_line_turn(
    event: dict[str, Any],
    *,
    fallback_ts: str,
) -> tuple[str, str, str] | None:
    """Return (role, text, timestamp) for one JSONL event, or None."""
    ts = event.get("timestamp") or event.get("created_at") or event.get("ts")
    timestamp = ts if isinstance(ts, str) and ts else fallback_ts

    if not event.get("type") and not event.get("payload"):
        legacy = (
            _extract_text(event.get("text"))
            or _extract_text(event.get("prompt"))
        )
        if legacy:
            return "user", legacy, timestamp

    event_type = event.get("type")
    payload = event.get("payload") or {}
    if event_type == "response_item" and payload.get("type") == "message":
        role = str(payload.get("role") or "").lower()
        if role not in {"user", "assistant"}:
            return None
        text = grader_lib._content_to_text(payload.get("content"))
        if not text:
            return None
        return role, text.strip(), timestamp

    if event_type == "event_msg":
        msg_type = payload.get("type")
        message = payload.get("message")
        if msg_type == "user_message" and isinstance(message, str) and message.strip():
            return "user", message.strip(), timestamp
        if msg_type == "agent_message" and isinstance(message, str) and message.strip():
            return "assistant", message.strip(), timestamp

    role = event.get("role")
    if role in {"user", "assistant"}:
        text = (
            _extract_text(event.get("text"))
            or _extract_text(event.get("message"))
            or grader_lib._content_to_text(event.get("content"))
        )
        if text:
            return str(role), text, timestamp

    return None


def _parse_codex_turns(path: Path) -> tuple[list[dict[str, Any]], int]:
    fallback_ts = file_mtime_iso(path)
    session_id = _codex_session_id(path)
    turns: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
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
            if event.get("type") == "session_meta":
                session_id = _codex_session_id(path, event)

            parsed = _extract_codex_line_turn(event, fallback_ts=fallback_ts)
            if parsed is None:
                continue
            role, text, timestamp = parsed
            processor = _process_learner_text if role == "user" else _process_assistant_text
            cleaned, notes = processor(text)
            if not cleaned:
                if role == "user" and "workflow_protocol_reply" in notes:
                    protocol_reply_excluded += 1
                continue
            if turns and turns[-1]["role"] == role and turns[-1]["text"] == cleaned:
                continue
            turn = _make_turn(
                session_id=session_id,
                turn_index=len(turns),
                role=role,
                text=cleaned,
                timestamp=timestamp,
                model_id=None,
            )
            turn["_redaction_notes"] = notes
            turns.append(turn)
    return turns, protocol_reply_excluded


def _parse_codex_candidates(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Read a Codex JSONL file and return user prompt candidates only."""
    turns, protocol_reply_excluded = _parse_codex_turns(path)
    if not turns:
        return [], protocol_reply_excluded
    file_mtime = file_mtime_iso(path)
    candidates: list[dict[str, Any]] = []
    for turn in turns:
        if turn["role"] != "user":
            continue
        candidates.append({
            "text": turn["text"],
            "timestamp": turn["timestamp"] or file_mtime,
            "source_tool": "codex",
            "model_hint": None,
            "_redaction_notes": turn.get("_redaction_notes") or [],
            "_file_mtime": file_mtime,
        })
    return candidates, protocol_reply_excluded


def scan_summary(results: list[dict[str, Any]], *, intake: dict[str, dict] | None = None) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    return claude_ad.scan_summary(results, intake=intake)
