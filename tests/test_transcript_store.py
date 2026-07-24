from domain import TurnRecord
import store


def _turn(i, session="s1"):
    return TurnRecord(
        source_tool="claude", session_id=session, turn_index=i, role="user",
        timestamp="2026-07-24T00:00:00Z", text_redacted=f"turn {i}",
        parser_confidence=1.0, analysis_eligible=True,
    )


def test_no_persist_writes_nothing(tmp_path):
    res = store.save_turns([_turn(0), _turn(1)], persist_transcripts=False, root=tmp_path)
    assert res["persisted"] == 0
    assert not (tmp_path / "transcripts.jsonl").exists()
    assert res["session_ids"] == ["s1"]


def test_persist_writes_redacted_turns(tmp_path):
    res = store.save_turns([_turn(0), _turn(1)], persist_transcripts=True, root=tmp_path)
    assert res["persisted"] == 2
    lines = (tmp_path / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "text_redacted" in lines[0]
    assert "prompt_text" not in lines[0]
