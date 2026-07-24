"""Measure whether redaction preserves the cause-distinguishing cues.

Gate for Phase 5: if redacted transcripts cannot preserve the tokens that
separate user_under_specified from agent_misread above GATE_THRESHOLD, the
band-affecting attribution in Phase 5 must not be enabled.
"""
from __future__ import annotations

import redact

GATE_THRESHOLD = 0.85


def _cues_survive(text: str, cue_tokens: list[str]) -> bool:
    redacted, _flags = redact.redact_text(text)
    low = redacted.lower()
    return all(tok.lower() in low for tok in cue_tokens)


def measure_fidelity(cases: list[dict]) -> dict:
    total = len(cases)
    survived = sum(1 for c in cases if _cues_survive(c["text"], c.get("cue_tokens", [])))
    return {
        "total": total,
        "distinguishable_after_redaction": survived,
        "rate": (survived / total) if total else 0.0,
    }
