from datetime import datetime, timedelta, timezone
from pathlib import Path

import consent
import domain
import paths
import purge_data
import retention
import store


def test_paths_grader_home_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    assert paths.grader_home() == tmp_path


def test_consent_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    assert consent.has_consent("claude") is False
    consent.grant_consent("claude")
    assert consent.has_consent("claude") is True


def test_save_grade_default_no_raw(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    store.save_grade(
        {"id": "g1", "prompt_id": "p1", "percent": 80, "band": "B"},
        persist_raw=False,
        raw_text="SECRET sk-ant-abcdefghijklmnopqrstuvwxyz123456",
        excerpt="hello",
    )
    assert not (tmp_path / "raw").exists() or not any((tmp_path / "raw").iterdir())
    assert (tmp_path / "excerpts" / "p1.txt").read_text(encoding="utf-8") == "hello"


def test_save_grade_persist_raw(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    store.save_grade(
        {"id": "g2", "prompt_id": "p2", "percent": 70, "band": "C"},
        persist_raw=True,
        raw_text="raw body",
        excerpt="excerpt body",
    )
    assert (tmp_path / "raw" / "p2.txt").read_text(encoding="utf-8") == "raw body"
    assert (tmp_path / "excerpts" / "p2.txt").read_text(encoding="utf-8") == "excerpt body"


def test_save_grade_accepts_dataclass_report(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    report = domain.GradeReport(
        id="g5",
        prompt_id="p5",
        dimension_scores=[domain.DimensionScore("D1", 2, 3)],
        earned=6.0,
        possible=9.0,
        percent=66.7,
        band="C",
        caps_applied=[],
    )
    store.save_grade(
        report,
        persist_raw=False,
        raw_text="raw",
        excerpt="excerpt",
    )
    grades = store.load_jsonl(tmp_path / "grades.jsonl")
    assert len(grades) == 1
    assert grades[0]["id"] == "g5"
    assert grades[0]["dimension_scores"][0]["dimension_id"] == "D1"
    assert (tmp_path / "excerpts" / "p5.txt").read_text(encoding="utf-8") == "excerpt"


def test_append_trend_metric_hash_chain(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    store.append_trend_metric({"metric_type": "band", "value": "C", "period": "day"})
    store.append_trend_metric({"metric_type": "band", "value": "B", "period": "day"})
    lines = (tmp_path / "metrics.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = store.load_jsonl_line(lines[0])
    second = store.load_jsonl_line(lines[1])
    assert first["hash"]
    assert second["hash"]
    assert second["hash"] != first["hash"]
    assert second["prev_hash"] == first["hash"]


def test_purge_expired_keeps_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    old = datetime.now(timezone.utc) - timedelta(days=31)
    store.save_grade(
        {"id": "g2", "prompt_id": "p2", "percent": 70, "band": "C", "ingested_at": old.isoformat()},
        persist_raw=True,
        raw_text="hi",
        excerpt="ex",
    )
    store.append_trend_metric({"metric_type": "band", "value": "C", "period": "day"})
    n = retention.purge_expired(days=30)
    assert n >= 1
    assert (tmp_path / "metrics.jsonl").is_file()
    assert not (tmp_path / "raw" / "p2.txt").exists()
    grades = store.load_jsonl(tmp_path / "grades.jsonl")
    assert len(grades) == 1
    assert "raw_path" not in grades[0]


def test_user_purge(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    store.save_grade(
        {"id": "g3", "prompt_id": "p3", "percent": 90, "band": "A"},
        persist_raw=True,
        raw_text="r",
        excerpt="e",
    )
    store.append_trend_metric({"metric_type": "count", "value": 1, "period": "day"})
    consent.grant_consent("claude")
    retention.user_purge(what={"raw", "excerpts", "metrics"})
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "excerpts").exists()
    assert not (tmp_path / "metrics.jsonl").exists()
    assert (tmp_path / "grades.jsonl").is_file()
    assert (tmp_path / "consent.json").is_file()


def test_strip_raw_fields_exact_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    record = {
        "id": "g1",
        "raw_path": "raw/g1.txt",
        "raw_text": "body",
        "persist_raw": True,
        "raw_score": 5,
        "foo": "bar",
    }
    stripped = retention._strip_raw_fields(record)
    assert "raw_path" not in stripped
    assert "raw_text" not in stripped
    assert "persist_raw" not in stripped
    assert stripped["raw_score"] == 5
    assert stripped["foo"] == "bar"


def test_user_purge_clears_raw_path_in_grades(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    store.save_grade(
        {"id": "g6", "prompt_id": "p6", "percent": 80, "band": "B"},
        persist_raw=True,
        raw_text="secret",
        excerpt="ex",
    )
    retention.user_purge(what={"raw"})
    grades = store.load_jsonl(tmp_path / "grades.jsonl")
    assert len(grades) == 1
    assert "raw_path" not in grades[0]
    assert grades[0]["percent"] == 80
    assert (tmp_path / "excerpts" / "p6.txt").exists()


def test_append_jsonl_creates_small_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    path = tmp_path / "test.jsonl"
    store.append_jsonl(path, {"a": 1})
    lines = store.load_jsonl(path)
    assert lines == [{"a": 1}]


def test_purge_data_cli_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))
    old = datetime.now(timezone.utc) - timedelta(days=31)
    store.save_grade(
        {"id": "g4", "prompt_id": "p4", "percent": 60, "band": "D", "ingested_at": old.isoformat()},
        persist_raw=True,
        raw_text="old",
        excerpt="oldex",
    )
    assert purge_data.main(["--expired"]) == 0
    assert not (tmp_path / "raw" / "p4.txt").exists()
