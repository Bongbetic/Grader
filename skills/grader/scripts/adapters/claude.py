"""Claude adapter: discover user prompts from the local Claude projects tree."""
from __future__ import annotations

from pathlib import Path

import consent
import grader_lib
import allowlist
import redact
from adapters import _make_turn, _process_assistant_text, _process_learner_text


def _process_prompt(text: str) -> tuple[str, list[str]]:
    return _process_learner_text(text)


def _discover_paths(paths: list[Path]) -> tuple[list[dict], int]:
    candidates: list[dict] = []
    protocol_reply_excluded = 0
    for path in paths:
        session = grader_lib.parse_session_jsonl(path)
        timestamp = session.get("started_at") or session.get("ended_at") or ""
        for prompt in session.get("user_prompts") or []:
            cleaned, notes = _process_prompt(prompt)
            if not cleaned:
                if "workflow_protocol_reply" in notes:
                    protocol_reply_excluded += 1
                continue
            candidates.append({
                "text": cleaned,
                "timestamp": timestamp,
                "source_tool": "claude",
                "model_hint": None,
                "_redaction_notes": notes,
            })
    return candidates, protocol_reply_excluded


def discover(*, limit: int = 100) -> list[dict]:
    """Return raw prompt candidates from Claude sessions.

    Raises ``PermissionError`` if the user has not granted consent for Claude.
    """
    if not consent.has_consent("claude"):
        raise PermissionError("Claude intake consent not granted")

    paths = allowlist.paths_for_tool("claude")
    paths = grader_lib.select_recent_sessions(paths, limit=limit)
    candidates, _excluded = _discover_paths(paths)
    return candidates


def intake_stats(*, limit: int = 100) -> dict:
    """Return session-limit vs full-corpus counts for scan summaries."""
    if not consent.has_consent("claude"):
        raise PermissionError("Claude intake consent not granted")

    paths = allowlist.paths_for_tool("claude")
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


def discover_turns(*, limit: int = 100) -> list[dict]:
    """Return session-structured user and assistant turns from Claude sessions."""
    if not consent.has_consent("claude"):
        raise PermissionError("Claude intake consent not granted")

    paths = allowlist.paths_for_tool("claude")
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    turns: list[dict] = []
    for path in paths:
        session = grader_lib.parse_session_turns(path)
        session_id = str(session.get("session_id") or path.stem)
        fallback_ts = session.get("started_at") or ""
        for raw in session.get("turns") or []:
            role = raw.get("role", "user")
            processor = _process_learner_text if role == "user" else _process_assistant_text
            cleaned, _notes = processor(raw.get("text") or "")
            if not cleaned:
                continue
            turns.append(_make_turn(
                session_id=session_id,
                turn_index=len(turns),
                role=role,
                text=cleaned,
                timestamp=str(raw.get("timestamp") or fallback_ts),
                model_id=None,
            ))
    return turns


def scan_summary(results: list[dict], *, intake: dict[str, dict] | None = None) -> dict:
    """Summarize a list of raw candidates by source tool."""
    tools: dict[str, dict] = {}
    for r in results:
        tool = r.get("source_tool", "unknown")
        ts = r.get("timestamp") or r.get("_file_mtime") or ""
        if tool not in tools:
            tools[tool] = {
                "tool": tool,
                "count": 0,
                "time_range": {"min": None, "max": None},
                "redaction_count": 0,
            }
        entry = tools[tool]
        entry["count"] += 1
        if ts:
            if entry["time_range"]["min"] is None or ts < entry["time_range"]["min"]:
                entry["time_range"]["min"] = ts
            if entry["time_range"]["max"] is None or ts > entry["time_range"]["max"]:
                entry["time_range"]["max"] = ts
        text = r.get("text") or ""
        _, notes = redact.redact_text(text)
        if notes:
            entry["redaction_count"] += 1
    if intake:
        for tool, meta in intake.items():
            if tool not in tools:
                tools[tool] = {
                    "tool": tool,
                    "count": 0,
                    "time_range": {"min": None, "max": None},
                    "redaction_count": 0,
                }
            tools[tool].update(meta)
    return {
        "tools": list(tools.values()),
        "total": len(results),
    }
