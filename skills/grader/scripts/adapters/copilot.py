"""Copilot adapter: best-effort discovery of Copilot chat prompts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import consent
import grader_lib
import allowlist
import redact
from adapters import _process_learner_text

# Best-effort flag exposed for summary reporting.
_partial: bool = False


def discover(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return raw prompt candidates from Copilot chat files.

    Best-effort: never raises on missing files or malformed data. Per-file parse
    failures are skipped; ``_partial`` is set when any file fails.
    """
    global _partial
    _partial = False

    if not consent.has_consent("copilot"):
        raise PermissionError("Copilot intake consent not granted")

    paths = allowlist.paths_for_tool("copilot", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)
    candidates, _excluded = _discover_paths(paths)
    return candidates


def intake_stats(*, home: Path | None = None, limit: int = 100) -> dict[str, Any]:
    """Return session-limit vs full-corpus counts for scan summaries."""
    if not consent.has_consent("copilot"):
        raise PermissionError("Copilot intake consent not granted")

    paths = allowlist.paths_for_tool("copilot", home=home)
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
    global _partial
    candidates: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
    for path in paths:
        try:
            file_candidates, excluded = _parse_copilot_file(path)
        except Exception:
            _partial = True
            continue
        protocol_reply_excluded += excluded
        candidates.extend(file_candidates)
    return candidates, protocol_reply_excluded


def _parse_copilot_file(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Parse a single Copilot chat file as JSONL/JSON.

    Returns candidates on success. Any malformed JSON causes an empty result.
    """
    global _partial
    prompts: list[dict[str, Any]] = []
    protocol_reply_excluded = 0
    timestamps: list[str] = []
    with path.open(encoding="utf-8", errors="ignore") as fh:
        raw = fh.read().strip()
    if not raw:
        return [], 0

    # Try to parse the whole file as JSON.
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError:
        # Fall back to line-by-line JSONL.
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        data = []
        for line in lines:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise exc from None
    if not isinstance(data, list):
        _partial = True
        return [], 0

    for event in data:
        if not isinstance(event, dict):
            _partial = True
            continue
        text = _extract_text(event)
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
            "source_tool": "copilot",
            "model_hint": None,
            "_redaction_notes": notes,
        })
        ts = event.get("timestamp") or event.get("created_at") or event.get("ts")
        if ts and isinstance(ts, str):
            timestamps.append(ts)

    if prompts and timestamps:
        for p in prompts:
            p["timestamp"] = timestamps[0]
    return prompts, protocol_reply_excluded


def _extract_text(event: dict[str, Any]) -> str | None:
    for key in ("text", "prompt", "message"):
        value = event.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
        if isinstance(value, dict):
            text = value.get("text") or value.get("prompt") or value.get("message")
            if text:
                return str(text).strip()
    return None


def scan_summary(results: list[dict[str, Any]], *, intake: dict[str, dict] | None = None) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    summary = claude_ad.scan_summary(results, intake=intake)
    if not results or _partial:
        summary["partial"] = True
    return summary
