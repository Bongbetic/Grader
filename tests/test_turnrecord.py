import pytest
from domain import TurnRecord


def _valid_kwargs(**over):
    base = dict(
        source_tool="claude",
        session_id="sess-1",
        turn_index=0,
        role="user",
        timestamp="2026-07-24T00:00:00Z",
        text_redacted="hello",
        model_id=None,
        workflow_marker=None,
        parser_confidence=1.0,
        analysis_eligible=True,
    )
    base.update(over)
    return base


def test_turnrecord_accepts_valid():
    tr = TurnRecord(**_valid_kwargs())
    assert tr.role == "user"
    assert tr.analysis_eligible is True


def test_turnrecord_rejects_negative_turn_index():
    with pytest.raises(ValueError, match="turn_index"):
        TurnRecord(**_valid_kwargs(turn_index=-1))


def test_turnrecord_rejects_bad_confidence():
    with pytest.raises(ValueError, match="parser_confidence"):
        TurnRecord(**_valid_kwargs(parser_confidence=1.5))


def test_turnrecord_rejects_unknown_role():
    with pytest.raises(ValueError, match="role"):
        TurnRecord(**_valid_kwargs(role="system"))
