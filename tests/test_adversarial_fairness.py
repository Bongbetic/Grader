from pathlib import Path
from gold_set import load_gold

BASE = Path(__file__).resolve().parents[1] / "skills" / "grader" / "fixtures" / "gold"


def test_adversarial_cases_are_low_banded():
    rows = load_gold(BASE / "adversarial.jsonl")
    assert rows
    assert all(r["human_band"] in ("C", "D") for r in rows)


def test_fairness_complete_cases_score_well():
    rows = load_gold(BASE / "fairness.jsonl")
    assert rows
    # information-complete prompts must not be failed for form
    assert all(r["human_band"] in ("A", "B") for r in rows)


def test_valid_continuation_not_penalized_for_brevity():
    rows = {r["id"]: r for r in load_gold(BASE / "fairness.jsonl")}
    tvc = rows["fair-terse-valid-continuation"]
    assert tvc["human_levels"]["D1"] >= 2  # terse but complete-in-context
    assert tvc["human_levels"]["D2"] == 2  # proportional D2, not zeroed for brevity
    assert tvc["human_band"] in ("A", "B")
