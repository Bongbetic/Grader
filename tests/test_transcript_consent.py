import consent


def test_transcript_consent_absent_by_default(tmp_path):
    assert consent.has_transcript_consent(root=tmp_path) is False


def test_grant_transcript_consent(tmp_path):
    consent.grant_transcript_consent(root=tmp_path)
    assert consent.has_transcript_consent(root=tmp_path) is True


def test_tool_intake_consent_does_not_imply_transcript(tmp_path):
    consent.grant_consent("claude", root=tmp_path)
    assert consent.has_consent("claude", root=tmp_path) is True
    assert consent.has_transcript_consent(root=tmp_path) is False
