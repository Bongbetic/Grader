from turn_intake import build_turn_records, detect_workflow_marker


def test_detects_slash_command():
    assert detect_workflow_marker("/brainstorm let's design X") == "slash:brainstorm"


def test_detects_namespaced_slash_command():
    assert detect_workflow_marker("/superpowers:writing-plans") == "slash:superpowers:writing-plans"


def test_detects_skill_announce():
    assert detect_workflow_marker("Using brainstorming to explore the idea") == "skill-announce:brainstorming"


def test_plain_prompt_has_no_marker():
    assert detect_workflow_marker("write a function that sorts a list") is None


def _raw(i, role="user", text="hello", session="s1"):
    return {"session_id": session, "turn_index": i, "role": role, "text": text}


def test_claude_turns_are_eligible_with_consent():
    raws = [_raw(0), _raw(1, text="/brainstorm plan it")]
    recs = build_turn_records(raws, source_tool="claude", consent_covers_transcript=True)
    assert len(recs) == 2
    assert all(r.analysis_eligible for r in recs)
    assert recs[1].workflow_marker == "slash:brainstorm"


def test_no_transcript_consent_makes_ineligible():
    recs = build_turn_records([_raw(0)], source_tool="claude", consent_covers_transcript=False)
    assert recs[0].analysis_eligible is False


def test_import_paste_is_ineligible_even_with_consent():
    recs = build_turn_records([_raw(0)], source_tool="import_paste", consent_covers_transcript=True)
    assert recs[0].analysis_eligible is False
    assert recs[0].parser_confidence < 0.5


def test_text_is_redacted():
    recs = build_turn_records(
        [_raw(0, text="my key sk-ant-ABCDEFGHIJKLMNOPQRSTUV token")],
        source_tool="claude", consent_covers_transcript=True,
    )
    assert "sk-ant-" not in recs[0].text_redacted
