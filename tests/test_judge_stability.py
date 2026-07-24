from judge_stability import classification_stability


def test_unanimous_is_one():
    runs = [{"task_complexity": "complex"} for _ in range(5)]
    assert classification_stability(runs)["task_complexity"] == 1.0


def test_split_lowers_agreement():
    runs = [
        {"rework_cause": "user_under_specified"},
        {"rework_cause": "user_under_specified"},
        {"rework_cause": "agent_misread"},
    ]
    assert classification_stability(runs)["rework_cause"] < 0.7
