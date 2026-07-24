"""Cursor adapter: discover user prompts from exported Cursor transcripts."""
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
    """Return raw prompt candidates from Cursor transcripts.

    Raises ``PermissionError`` if the user has not granted consent for Cursor.
    """
    if not consent.has_consent("cursor"):
        raise PermissionError("Cursor intake consent not granted")

    paths = allowlist.paths_for_tool("cursor", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)
    candidates, _excluded = _discover_paths(paths)
    return candidates


def intake_stats(*, home: Path | None = None, limit: int = 100) -> dict[str, Any]:
    """Return session-limit vs full-corpus counts for scan summaries."""
    if not consent.has_consent("cursor"):
        raise PermissionError("Cursor intake consent not granted")

    paths = allowlist.paths_for_tool("cursor", home=home)
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
        if path.suffix in {".jsonl", ".json"}:
            file_candidates, excluded = _parse_cursor_jsonl(path)
        elif path.suffix == ".txt":
            file_candidates, excluded = _parse_txt_candidates(path)
        else:
            continue
        protocol_reply_excluded += excluded
        candidates.extend(file_candidates)
    return candidates, protocol_reply_excluded


def discover_turns(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return session-structured user and assistant turns from Cursor transcripts."""
    if not consent.has_consent("cursor"):
        raise PermissionError("Cursor intake consent not granted")

    paths = allowlist.paths_for_tool("cursor", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    turns: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix not in {".jsonl", ".json"}:
            continue
        turns.extend(_parse_cursor_turns(path))
    return turns


def _cursor_session_id(path: Path) -> str:
    if path.parent.name == "agent-transcripts":
        return path.stem
    return path.parent.name


def _parse_cursor_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Parse Cursor agent-transcript JSONL (role + message.content[] shape)."""
    prompts: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
    timestamps: list[str] = []
    fallback_ts = file_mtime_iso(path)
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
                if "workflow_protocol_reply" in notes:
                    protocol_reply_excluded += 1
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
        return [], protocol_reply_excluded
    timestamp = timestamps[0] if timestamps else fallback_ts
    file_mtime = fallback_ts
    for prompt in prompts:
        prompt["timestamp"] = timestamp
        prompt["_file_mtime"] = file_mtime
    return prompts, protocol_reply_excluded


def _parse_cursor_turns(path: Path) -> list[dict[str, Any]]:
    """Parse Cursor agent-transcript JSONL into ordered user+assistant turns."""
    session_id = _cursor_session_id(path)
    fallback_ts = file_mtime_iso(path)
    turns: list[dict[str, Any]] = []
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
            if role is None:
                if event.get("text") or event.get("prompt"):
                    role = "user"
                else:
                    continue
            role = str(role).lower()
            if role not in {"user", "assistant"}:
                continue

            text = _extract_cursor_text(event)
            if not text:
                continue

            processor = _process_learner_text if role == "user" else _process_assistant_text
            cleaned, _notes = processor(text)
            if not cleaned:
                continue
            if turns and turns[-1]["role"] == role and turns[-1]["text"] == cleaned:
                continue

            ts = event.get("timestamp") or event.get("created_at") or event.get("ts")
            timestamp = ts if isinstance(ts, str) and ts else fallback_ts
            turns.append(_make_turn(
                session_id=session_id,
                turn_index=len(turns),
                role=role,
                text=cleaned,
                timestamp=timestamp,
                model_id=None,
            ))
    return turns


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


def _parse_txt_candidates(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Treat each non-empty line of a .txt transcript as a prompt."""
    candidates: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            cleaned, notes = _process_learner_text(text)
            if not cleaned:
                if "workflow_protocol_reply" in notes:
                    protocol_reply_excluded += 1
                continue
            candidates.append({
                "text": cleaned,
                "timestamp": "",
                "source_tool": "cursor",
                "model_hint": None,
                "_redaction_notes": notes,
            })
    file_mtime = file_mtime_iso(path)
    for candidate in candidates:
        candidate["timestamp"] = file_mtime
        candidate["_file_mtime"] = file_mtime
    return candidates, protocol_reply_excluded


def scan_summary(results: list[dict[str, Any]], *, intake: dict[str, dict] | None = None) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    return claude_ad.scan_summary(results, intake=intake)
