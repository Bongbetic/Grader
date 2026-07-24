"""Normalize raw intake candidates into ``PromptRecord`` instances."""
from __future__ import annotations

import hashlib

import model_class
import redact
from domain import PromptRecord

_EXCERPT_LENGTH = 240


def _prompt_id(text: str, source_tool: str, timestamp: str) -> str:
    payload = f"{source_tool}|{timestamp}|{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def to_prompt_record(candidate: dict, *, persist_raw: bool = False) -> PromptRecord:
    """Convert a raw candidate dict into a redacted ``PromptRecord``."""
    text = candidate.get("text") or ""
    source_tool = candidate.get("source_tool", "unknown")
    timestamp = candidate.get("timestamp") or ""
    model_hint = candidate.get("model_hint")

    redacted_text, flags = redact.redact_text(text)
    excerpt = redacted_text[:_EXCERPT_LENGTH]

    return PromptRecord(
        id=_prompt_id(text, source_tool, timestamp),
        prompt_text=redacted_text if persist_raw else None,
        redacted_text=redacted_text,
        redacted_excerpt=excerpt,
        source_tool=source_tool,
        timestamp=timestamp,
        target_model_class=model_class.classify(model_hint),
        redaction_flags=flags,
        persist_raw=persist_raw,
    )
