"""Canonical TurnRecord intake: workflow detection, confidence, eligibility."""
from __future__ import annotations

import re

import redact
from capability_matrix import capabilities_for, supports_session_analysis
from domain import TurnRecord

_SLASH = re.compile(r"^\s*/([a-zA-Z][\w:-]*)")
_SKILL_ANNOUNCE = re.compile(r"(?i)\busing\s+([a-z][\w-]*)\s+to\b")

_CONFIDENCE_THRESHOLD = 0.5


def detect_workflow_marker(text: str) -> str | None:
    """Detect a workflow/command marker in a single turn's text.

    Returns a normalized marker string or None. Deterministic; no LLM.
    """
    if not text:
        return None
    m = _SLASH.match(text)
    if m:
        return f"slash:{m.group(1)}"
    if "<command-name>" in text:
        cm = re.search(r"<command-name>\s*/?([\w:-]+)", text)
        if cm:
            return f"command-name:{cm.group(1)}"
    sm = _SKILL_ANNOUNCE.search(text)
    if sm:
        return f"skill-announce:{sm.group(1)}"
    return None


def build_turn_records(
    raw_turns: list[dict],
    *,
    source_tool: str,
    consent_covers_transcript: bool,
) -> list[TurnRecord]:
    """Convert raw adapter turns into canonical, redacted TurnRecords.

    - Drops assistant turns when the adapter cannot preserve assistant text.
    - Sets analysis_eligible only when the adapter supports session analysis,
      consent covers transcript analysis, and parser confidence is adequate.
    """
    cap = capabilities_for(source_tool)
    session_ok = supports_session_analysis(source_tool)
    confidence = 1.0 if cap.role else 0.3
    records: list[TurnRecord] = []
    for raw in raw_turns:
        role = raw.get("role", "user")
        if role == "assistant" and not cap.assistant_text:
            continue
        text_redacted, _flags = redact.redact_text(raw.get("text") or "")
        eligible = (
            session_ok
            and consent_covers_transcript
            and confidence >= _CONFIDENCE_THRESHOLD
        )
        records.append(
            TurnRecord(
                source_tool=source_tool,
                session_id=str(raw.get("session_id", "")),
                turn_index=int(raw.get("turn_index", 0)),
                role=role,
                timestamp=str(raw.get("timestamp", "")),
                text_redacted=text_redacted,
                model_id=raw.get("model_id"),
                workflow_marker=detect_workflow_marker(raw.get("text") or ""),
                parser_confidence=confidence,
                analysis_eligible=eligible,
            )
        )
    return records
