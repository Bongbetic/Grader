"""Validate the judge's classification block (evidence + confidence + abstention).

The judge (host LLM) emits these labels; Python only validates structure and
vocabulary. Deterministic counters never set these — they are candidate signals.
"""
from __future__ import annotations

from typing import Any

TASK_COMPLEXITY = frozenset({"trivial", "simple", "moderate", "complex"})
PROMPT_CLASS = frozenset({
    "standalone", "valid_continuation", "lazy_delegation",
    "execution_handoff_gap", "workflow_protocol_reply",
})
FOLLOW_UP_TYPE = frozenset({
    "clarification_answer", "correction_of_agent_error", "result_driven_iteration",
    "new_constraint", "preference_change", "protocol_reply",
    "restate_unmet_intent", "abandonment",
})
SCOPE_CHANGE = frozenset({
    "planned_decomposition", "additive_feature", "adaptive_change_with_evidence",
    "scope_change_without_prior_signal", "under_specified_initial_plan",
})
REWORK_CAUSE = frozenset({
    "user_under_specified", "agent_misread", "tool_or_environment",
    "new_information", "user_preference_change", "indeterminate",
})
CONFIDENCE = frozenset({"low", "medium", "high"})

_FIELD_VOCAB = {
    "task_complexity": TASK_COMPLEXITY,
    "prompt_class": PROMPT_CLASS,
    "follow_up_type": FOLLOW_UP_TYPE,
    "scope_change": SCOPE_CHANGE,
    "rework_cause": REWORK_CAUSE,
}
_REQUIRED_FIELDS = ("task_complexity",)


def _validate_entry(field: str, entry: Any, vocab: frozenset[str]) -> dict:
    if not isinstance(entry, dict):
        raise ValueError(f"{field} must be an object")
    value = entry.get("value")
    if value not in vocab:
        raise ValueError(f"{field} value must be one of {sorted(vocab)}")
    ev = entry.get("evidence_span")
    if not isinstance(ev, str) or not ev.strip():
        raise ValueError(f"{field} missing evidence_span")
    conf = entry.get("confidence")
    if conf not in CONFIDENCE:
        raise ValueError(f"{field} confidence must be one of {sorted(CONFIDENCE)}")
    return {"value": value, "evidence_span": ev, "confidence": conf}


def parse_classification(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("classification must be a JSON object")
    version = data.get("classifier_version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("classification missing classifier_version")

    out: dict[str, Any] = {"classifier_version": version}
    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"classification missing required field {field}")
    for field, vocab in _FIELD_VOCAB.items():
        if field in data:
            out[field] = _validate_entry(field, data[field], vocab)
    return out
