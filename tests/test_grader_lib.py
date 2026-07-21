import grader_lib
from grader_lib import redact_secrets


def test_redact_sk_api_key_pattern():
    raw = "use key sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789abcdefghij"
    cleaned, notes = redact_secrets(raw)
    assert "sk-ant-api03-" not in cleaned
    assert "[REDACTED_SECRET]" in cleaned
    assert notes  # non-empty


def test_redact_leaves_normal_prompt():
    raw = "Add dark mode toggle to settings"
    cleaned, notes = redact_secrets(raw)
    assert cleaned == raw
    assert notes == []


def test_default_session_limit_is_30():
    assert grader_lib.DEFAULT_SESSION_LIMIT == 30


def test_empty_dossier_schema():
    d = grader_lib.empty_dossier("auto")
    assert d["intake_path"] == "auto"
    assert d["sessions_found"] == 0
    assert d["sessions_graded"] == 0
    assert d["sessions"] == []
    assert d["redaction_notes"] == []
