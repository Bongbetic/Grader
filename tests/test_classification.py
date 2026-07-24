import pytest
from classification import (
    TASK_COMPLEXITY, PROMPT_CLASS, FOLLOW_UP_TYPE,
    SCOPE_CHANGE, REWORK_CAUSE, CONFIDENCE,
    parse_classification,
)


def test_vocabularies_present():
    assert "complex" in TASK_COMPLEXITY
    assert "workflow_protocol_reply" in PROMPT_CLASS
    assert "restate_unmet_intent" in FOLLOW_UP_TYPE
    assert "adaptive_change_with_evidence" in SCOPE_CHANGE
    assert "indeterminate" in REWORK_CAUSE
    assert CONFIDENCE == frozenset({"low", "medium", "high"})


def _entry(value, conf="high", ev="because X"):
    return {"value": value, "evidence_span": ev, "confidence": conf}


def _valid_block(**over):
    block = {
        "classifier_version": "grader-judge-2026-07-24",
        "task_complexity": _entry("complex"),
        "prompt_class": _entry("standalone"),
    }
    block.update(over)
    return block


def test_valid_block_parses():
    out = parse_classification(_valid_block())
    assert out["task_complexity"]["value"] == "complex"
    assert out["classifier_version"] == "grader-judge-2026-07-24"


def test_missing_classifier_version_rejected():
    block = _valid_block()
    del block["classifier_version"]
    with pytest.raises(ValueError, match="classifier_version"):
        parse_classification(block)


def test_missing_evidence_span_rejected():
    with pytest.raises(ValueError, match="evidence_span"):
        parse_classification(_valid_block(task_complexity={"value": "complex", "confidence": "high"}))


def test_unknown_value_rejected():
    with pytest.raises(ValueError, match="task_complexity"):
        parse_classification(_valid_block(task_complexity=_entry("gigantic")))


def test_bad_confidence_rejected():
    with pytest.raises(ValueError, match="confidence"):
        parse_classification(_valid_block(task_complexity=_entry("complex", conf="certain")))


def test_indeterminate_rework_cause_allowed():
    out = parse_classification(_valid_block(rework_cause=_entry("indeterminate")))
    assert out["rework_cause"]["value"] == "indeterminate"
