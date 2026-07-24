import json
from pathlib import Path
from redaction_fidelity import measure_fidelity, GATE_THRESHOLD

FIXTURE = Path(__file__).resolve().parents[1] / "skills" / "grader" / "fixtures" / "redaction_fidelity" / "labeled_reworks.jsonl"


def _load():
    return [json.loads(l) for l in FIXTURE.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_seed_fixture_clears_gate():
    result = measure_fidelity(_load())
    assert result["total"] == 4
    assert result["rate"] >= GATE_THRESHOLD


def test_redaction_of_secret_does_not_destroy_cue():
    cases = [{"id": "x", "label": "user_under_specified",
              "text": "I meant use key sk-ant-ABCDEFGHIJKLMNOPQRSTUV not the old one",
              "cue_tokens": ["meant", "not"]}]
    result = measure_fidelity(cases)
    assert result["distinguishable_after_redaction"] == 1
