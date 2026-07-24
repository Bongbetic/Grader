import json
from pathlib import Path
from classification import parse_classification

SCHEMA = Path(__file__).resolve().parents[1] / "skills" / "grader" / "references" / "judge-schema.json"


def test_schema_documents_classification():
    text = SCHEMA.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert "classification" in json.dumps(doc)


def test_schema_example_parses():
    example = {
        "classifier_version": "grader-judge-2026-07-24",
        "task_complexity": {"value": "moderate", "evidence_span": "build a small CLI", "confidence": "medium"},
        "prompt_class": {"value": "standalone", "evidence_span": "single self-contained ask", "confidence": "high"},
    }
    out = parse_classification(example)
    assert out["task_complexity"]["value"] == "moderate"
