import grader_lib


def test_default_session_limit_is_30():
    assert grader_lib.DEFAULT_SESSION_LIMIT == 30


def test_empty_dossier_schema():
    d = grader_lib.empty_dossier("auto")
    assert d["intake_path"] == "auto"
    assert d["sessions_found"] == 0
    assert d["sessions_graded"] == 0
    assert d["sessions"] == []
    assert d["redaction_notes"] == []
