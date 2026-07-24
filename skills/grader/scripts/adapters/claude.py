"""Claude adapter: discover user prompts from the local Claude projects tree."""
from __future__ import annotations

import consent
import grader_lib
import allowlist
import redact
from adapters import _process_learner_text


def _process_prompt(text: str) -> tuple[str, list[str]]:
    return _process_learner_text(text)


def discover(*, limit: int = 100) -> list[dict]:
    """Return raw prompt candidates from Claude sessions.

    Raises ``PermissionError`` if the user has not granted consent for Claude.
    """
    if not consent.has_consent("claude"):
        raise PermissionError("Claude intake consent not granted")

    paths = allowlist.paths_for_tool("claude")
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    candidates: list[dict] = []
    for path in paths:
        session = grader_lib.parse_session_jsonl(path)
        timestamp = session.get("started_at") or session.get("ended_at") or ""
        for prompt in session.get("user_prompts") or []:
            cleaned, notes = _process_prompt(prompt)
            if not cleaned:
                continue
            candidates.append({
                "text": cleaned,
                "timestamp": timestamp,
                "source_tool": "claude",
                "model_hint": None,
                "_redaction_notes": notes,
            })
    return candidates


def discover_turns(*, limit: int = 100) -> list[dict]:
    """Return session-structured user turns from Claude sessions.

    Companion to discover(); preserves session_id + turn_index so downstream
    code can build canonical TurnRecords. User turns only (the adapter does not
    preserve assistant text — see capability matrix).
    """
    if not consent.has_consent("claude"):
        raise PermissionError("Claude intake consent not granted")

    paths = allowlist.paths_for_tool("claude")
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    turns: list[dict] = []
    for path in paths:
        session = grader_lib.parse_session_jsonl(path)
        session_id = str(session.get("session_id") or getattr(path, "stem", None) or path)
        timestamp = session.get("started_at") or session.get("ended_at") or ""
        for idx, prompt in enumerate(session.get("user_prompts") or []):
            cleaned, _notes = _process_prompt(prompt)
            if not cleaned:
                continue
            turns.append({
                "session_id": session_id,
                "turn_index": idx,
                "role": "user",
                "text": cleaned,
                "timestamp": timestamp,
                "model_id": None,
            })
    return turns


def scan_summary(results: list[dict]) -> dict:
    """Summarize a list of raw candidates by source tool."""
    tools: dict[str, dict] = {}
    for r in results:
        tool = r.get("source_tool", "unknown")
        ts = r.get("timestamp") or ""
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
    return {
        "tools": list(tools.values()),
        "total": len(results),
    }
