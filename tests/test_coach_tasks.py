import random
from collections import Counter

import pytest

from coach_tasks import load_coach_tasks, select_live_assessment


REQUIRED_FIELDS = {
    "id",
    "complexity",
    "title",
    "problem",
    "must_cover",
    "failure_modes",
}


def test_load_coach_tasks_bank_schema_and_counts():
    tasks = load_coach_tasks()
    counts = Counter(task["complexity"] for task in tasks)

    assert counts["easy"] >= 3
    assert counts["medium"] >= 4
    assert counts["hard"] >= 3
    assert len({task["id"] for task in tasks}) == len(tasks)
    for task in tasks:
        assert REQUIRED_FIELDS <= set(task)
        assert task["complexity"] in {"easy", "medium", "hard"}
        assert task["title"]
        assert task["problem"]
        assert task["must_cover"]
        assert task["failure_modes"]
        assert all(isinstance(item, str) and item for item in task["must_cover"])
        assert all(isinstance(item, str) and item for item in task["failure_modes"])


def test_select_live_assessment_mix():
    tasks = load_coach_tasks()
    picked = select_live_assessment(tasks, rng=random.Random(123))

    complexities = [task["complexity"] for task in picked]
    assert complexities.count("easy") == 1
    assert complexities.count("medium") == 2
    assert complexities.count("hard") == 1
    assert len({task["id"] for task in picked}) == 4


def test_select_live_assessment_rng_is_injectable():
    tasks = load_coach_tasks()

    first = select_live_assessment(tasks, rng=random.Random(77))
    second = select_live_assessment(tasks, rng=random.Random(77))

    assert [task["id"] for task in first] == [task["id"] for task in second]


def test_select_live_assessment_requires_enough_tasks():
    tasks = [
        {"id": "easy-1", "complexity": "easy"},
        {"id": "medium-1", "complexity": "medium"},
        {"id": "hard-1", "complexity": "hard"},
    ]

    with pytest.raises(ValueError, match="medium"):
        select_live_assessment(tasks, rng=random.Random(1))
