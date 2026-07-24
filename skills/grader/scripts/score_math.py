# skills/grader/scripts/score_math.py
from __future__ import annotations

from calibration_gate import calibration_gate_ok
from domain import (
    DISQUALIFIER_IDS,
    NA,
    DimensionScore,
    GradeBand,
    TargetModelClass,
)

_BAND_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
_ONE_DOWN = {"A": "B", "B": "C", "C": "C"}  # C never drops to D from signals


def band_from_percent(percent: float) -> GradeBand:
    if percent >= 90:
        return "A"
    if percent >= 75:
        return "B"
    if percent >= 60:
        return "C"
    return "D"


def _worse_band(a: GradeBand, b: GradeBand) -> GradeBand:
    """Return the worse (lower) grade band."""
    return a if _BAND_ORDER[a] > _BAND_ORDER[b] else b


def finalize(
    scores: list[DimensionScore],
    *,
    disqualifier_flags: list[str],
    target_model_class: TargetModelClass,
) -> tuple[float, float, float, GradeBand, list[str]]:
    earned = 0.0
    possible = 0.0
    for s in scores:
        if s.level == NA:
            continue
        if s.dimension_id == "D5" and target_model_class == "unknown":
            continue  # D5 not assessable when class is unknown -> N/A, not capped
        level = int(s.level)
        earned += level * s.weight
        possible += 3 * s.weight
    if possible <= 0:
        raise ValueError("no applicable dimensions")
    percent = earned / possible * 100.0
    band = band_from_percent(percent)

    flags = [f for f in disqualifier_flags if f in DISQUALIFIER_IDS]
    if target_model_class == "unknown":
        flags = [f for f in flags if f != "wrong_model_class"]
    caps_applied: list[str] = []
    for f in flags:
        caps_applied.append(f)
        band = _worse_band(band, "C")
    return earned, possible, percent, band, caps_applied


def apply_outcome_modifier(
    band,
    *,
    efficacy,
    planning,
    efficacy_high_confidence_user_underspec: bool,
    planning_high_confidence_underspec: bool,
    mean_kappa,
):
    """Lower the band at most one letter for same-task, high-confidence,
    user-attributable outcome evidence. Never promotes; never reaches D from
    signals alone; gated on calibration."""
    if not calibration_gate_ok(mean_kappa):
        return band, "no_change"
    if band == "D":
        return band, "no_change"

    reasons: list[str] = []
    if efficacy_high_confidence_user_underspec and (
        efficacy.attributed_rework_rate >= 0.5 or efficacy.worst_task_prompt_count >= 4
    ):
        reasons.append("efficacy:user_under_specified")
    if planning_high_confidence_underspec and planning.under_specified_initial_plan >= 1:
        reasons.append("planning:under_specified_initial_plan")

    if not reasons:
        return band, "no_change"
    return _ONE_DOWN[band], "; ".join(reasons)
