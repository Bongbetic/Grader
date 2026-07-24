from domain import EfficacyReport, PlanningReport, TaskReport


def test_efficacy_report_fields():
    r = EfficacyReport(
        session_id="s1", prompts_per_task_mean=2.0, single_shot_rate=0.5,
        attributed_rework_rate=0.25, worst_task_prompt_count=4,
        restates=1, corrections=0, abandoned_goal=False,
    )
    assert r.attributed_rework_rate == 0.25


def test_planning_report_counts():
    p = PlanningReport(
        session_id="s1", planned_decomposition=2, additive_feature=1,
        adaptive_change_with_evidence=1, scope_change_without_prior_signal=0,
        under_specified_initial_plan=1,
    )
    assert p.under_specified_initial_plan == 1


def test_task_report_binds_outcome_to_opening_prompt():
    e = EfficacyReport("s1", 1.0, 1.0, 0.0, 1, 0, 0, False)
    p = PlanningReport("s1", 0, 0, 0, 0, 0)
    t = TaskReport(
        session_id="s1", opening_prompt_id="pid-abc", craft_band="B",
        efficacy=e, planning=p, classifier_version="v1", evidence_spans=["x"],
    )
    assert t.opening_prompt_id == "pid-abc"
    assert t.efficacy.session_id == "s1"
