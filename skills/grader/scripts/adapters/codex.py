"""Codex adapter: discover user prompts from local Codex sessions."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import consent
import grader_lib
import allowlist
from adapters import _parse_jsonl_candidates


def discover(*, home: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return raw prompt candidates from Codex sessions.

    Raises ``PermissionError`` if the user has not granted consent for Codex.
    """
    if not consent.has_consent("codex"):
        raise PermissionError("Codex intake consent not granted")

    paths = allowlist.paths_for_tool("codex", home=home)
    paths = grader_lib.select_recent_sessions(paths, limit=limit)

    candidates: list[dict[str, Any]] = []
    for path in paths:
        candidates.extend(_parse_jsonl_candidates(path, source_tool="codex"))
    return candidates


def scan_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize a list of raw candidates by source tool."""
    from adapters import claude as claude_ad

    return claude_ad.scan_summary(results)
