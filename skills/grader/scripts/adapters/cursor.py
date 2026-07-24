"""Cursor adapter: discover user prompts from exported Cursor transcripts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import consent
import grader_lib
import allowlist
from adapters import _parse_jsonl_candidates


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
            candidates.extend(_parse_jsonl_candidates(path, source_tool="cursor"))
        elif path.suffix == ".txt":
            candidates.extend(_parse_txt_candidates(path))
    return candidates


def _parse_txt_candidates(path: Path) -> list[dict[str, Any]]:
    """Treat each non-empty line of a .txt transcript as a prompt."""
    candidates: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            cleaned, notes = grader_lib.redact_secrets(text)
            cleaned, tnotes = grader_lib.truncate_prompt(cleaned)
            candidates.append({
                "text": cleaned,
                "timestamp": "",
                "source_tool": "cursor",
                "model_hint": None,
                "_redaction_notes": list({n for n in notes + tnotes}),
            })
    return candidates


def scan_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    return claude_ad.scan_summary(results)
