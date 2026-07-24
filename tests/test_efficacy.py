from efficacy import build_efficacy_report


def _tasks():
    # two tasks; task 0 has a restate, task 1 is single-shot
    return {
        "prompts_per_task_mean": 1.5,
        "single_shot_rate": 0.5,
        "rework_rate": 0.5,
        "worst_task": {"prompt_count": 2},
        "tasks": [
            {"prompt_count": 2, "corrections": 0, "restates": 1, "resolved": True, "prompt_indices": [0, 1]},
            {"prompt_count": 1, "corrections": 0, "restates": 0, "resolved": True, "prompt_indices": [2]},
        ],
    }


def test_user_attributed_restate_counts():
    labels = {(0, 1): {"value": "restate_unmet_intent", "cause": "user_under_specified"}}
    r = build_efficacy_report("s1", _tasks(), labels)
    assert r.attributed_rework_rate == 0.5
    assert r.restates == 1


def test_agent_misread_restate_not_attributed():
    labels = {(0, 1): {"value": "restate_unmet_intent", "cause": "agent_misread"}}
    r = build_efficacy_report("s1", _tasks(), labels)
    assert r.attributed_rework_rate == 0.0  # not the user's craft failure
    assert r.restates == 1  # still reported as raw context


def test_result_driven_iteration_never_counts():
    labels = {(0, 1): {"value": "result_driven_iteration", "cause": "new_information"}}
    r = build_efficacy_report("s1", _tasks(), labels)
    assert r.attributed_rework_rate == 0.0
