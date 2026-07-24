"""Scope-change / planning report (report-only; no band effect in this phase)."""
from __future__ import annotations

from classification import SCOPE_CHANGE
from domain import PlanningReport


def build_planning_report(session_id: str, scope_change_labels: list[dict]) -> PlanningReport:
    counts = {cat: 0 for cat in SCOPE_CHANGE}
    for label in scope_change_labels:
        value = label.get("value")
        if value in counts:
            counts[value] += 1
    return PlanningReport(
        session_id=session_id,
        planned_decomposition=counts["planned_decomposition"],
        additive_feature=counts["additive_feature"],
        adaptive_change_with_evidence=counts["adaptive_change_with_evidence"],
        scope_change_without_prior_signal=counts["scope_change_without_prior_signal"],
        under_specified_initial_plan=counts["under_specified_initial_plan"],
    )
