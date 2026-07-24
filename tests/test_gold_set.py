from pathlib import Path
from gold_set import load_gold

SEED = Path(__file__).resolve().parents[1] / "skills" / "grader" / "fixtures" / "gold" / "seed.jsonl"


def test_load_gold_shape():
    rows = load_gold(SEED)
    assert len(rows) >= 4
    r = rows[0]
    for key in ("id", "prompt", "task_type", "model_class", "language", "human_levels", "human_band", "tags"):
        assert key in r
    assert set(r["human_levels"]).issuperset({f"D{i}" for i in range(1, 12)})


def test_seed_has_fairness_and_adversarial_tags():
    rows = load_gold(SEED)
    tags = {t for r in rows for t in r["tags"]}
    assert "fairness" in tags
    assert "adversarial" in tags
