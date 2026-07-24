from planning import build_planning_report


def test_counts_by_category():
    labels = [
        {"value": "planned_decomposition"},
        {"value": "planned_decomposition"},
        {"value": "adaptive_change_with_evidence"},
        {"value": "under_specified_initial_plan"},
    ]
    p = build_planning_report("s1", labels)
    assert p.planned_decomposition == 2
    assert p.adaptive_change_with_evidence == 1
    assert p.under_specified_initial_plan == 1
    assert p.scope_change_without_prior_signal == 0


def test_empty_is_all_zero():
    p = build_planning_report("s1", [])
    assert (p.planned_decomposition, p.under_specified_initial_plan) == (0, 0)


def test_unknown_value_ignored():
    p = build_planning_report("s1", [{"value": "not_a_category"}])
    assert p.planned_decomposition == 0
