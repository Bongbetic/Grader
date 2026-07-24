import retention


def test_all_purges_transcripts(tmp_path):
    (tmp_path / "transcripts.jsonl").write_text('{"a":1}\n', encoding="utf-8")
    retention.user_purge(root=tmp_path, what={"all"})
    assert not (tmp_path / "transcripts.jsonl").exists()


def test_verify_purged_reports_true_when_gone(tmp_path):
    (tmp_path / "transcripts.jsonl").write_text('{"a":1}\n', encoding="utf-8")
    retention.user_purge(root=tmp_path, what={"transcripts"})
    result = retention.verify_purged(tmp_path, categories={"transcripts"})
    assert result["transcripts"] is True


def test_verify_purged_reports_false_when_present(tmp_path):
    (tmp_path / "transcripts.jsonl").write_text('{"a":1}\n', encoding="utf-8")
    result = retention.verify_purged(tmp_path, categories={"transcripts"})
    assert result["transcripts"] is False
