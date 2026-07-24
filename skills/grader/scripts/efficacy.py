"""Attributed efficacy report (report-only; no band effect in this phase)."""
from __future__ import annotations

from domain import EfficacyReport


def build_efficacy_report(session_id: str, efficiency: dict, follow_up_labels: dict) -> EfficacyReport:
    """Build an EfficacyReport for one session.

    attributed_rework_rate counts ONLY tasks with a restate_unmet_intent
    follow-up attributed to user_under_specified. Other causes are context.
    """
    tasks = efficiency.get("tasks", [])
    total = len(tasks)
    attributed_tasks = 0
    total_restates = 0
    total_corrections = 0
    for task_index, task in enumerate(tasks):
        total_restates += task.get("restates", 0)
        total_corrections += task.get("corrections", 0)
        user_rework = False
        for turn_index in task.get("prompt_indices", []):
            label = follow_up_labels.get((task_index, turn_index))
            if (
                label
                and label.get("value") == "restate_unmet_intent"
                and label.get("cause") == "user_under_specified"
            ):
                user_rework = True
        if user_rework:
            attributed_tasks += 1

    worst = efficiency.get("worst_task") or {}
    return EfficacyReport(
        session_id=session_id,
        prompts_per_task_mean=efficiency.get("prompts_per_task_mean", 0.0),
        single_shot_rate=efficiency.get("single_shot_rate", 0.0),
        attributed_rework_rate=(attributed_tasks / total) if total else 0.0,
        worst_task_prompt_count=worst.get("prompt_count", 0),
        restates=total_restates,
        corrections=total_corrections,
        abandoned_goal=any(not t.get("resolved", True) for t in tasks),
    )
