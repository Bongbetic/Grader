"""Seam: attach_outcome_axes — craft GradeReport + optional outcome JSON → flat report dict."""
from __future__ import annotations

import dataclasses

import pytest
from domain import DIMENSION_WEIGHTS, DimensionScore, GradeReport
from finalize_grade import attach_outcome_axes

FLOOR_OK = 0.7


def _craft(band: str = "A", percent: float = 91.67) -> GradeReport:
    scores = [
        DimensionScore(d, 3 if d not in ("D5", "D7") else 2, DIMENSION_WEIGHTS[d])
        for d in DIMENSION_WEIGHTS
    ]
    # N/A conditionals for a simpler fixture shape where needed — use all scored
    return GradeReport(
        id="rid",
        prompt_id="p-1",
        dimension_scores=scores,
        earned=50.0,
        possible=54.0,
        percent=percent,
        band=band,  # type: ignore[arg-type]
        caps_applied=[],
        rationales={},
    )


def _eff_payload(**overrides):
    base = {
        "session_id": "s1",
        "prompts_per_task_mean": 3.2,
        "single_shot_rate": 0.25,
        "attributed_rework_rate": 0.5,
        "worst_task_prompt_count": 4,
        "restates": 2,
        "corrections": 1,
        "abandoned_goal": False,
        "high_confidence_user_underspec": True,
    }
    base.update(overrides)
    return base


def _plan_payload(**overrides):
    base = {
        "session_id": "s1",
        "planned_decomposition": 1,
        "additive_feature": 0,
        "adaptive_change_with_evidence": 0,
        "scope_change_without_prior_signal": 1,
        "under_specified_initial_plan": 1,
        "high_confidence_underspec": False,
    }
    base.update(overrides)
    return base


def test_both_absent_unavailable_no_modifier():
    out = attach_outcome_axes(_craft("A"), efficacy=None, planning=None, mean_kappa=FLOOR_OK)
    assert out["band_raw"] == "A"
    assert out["band"] == "A"
    assert out["modifier_reason"] == "no_change"
    assert out["efficacy"] == {"status": "unavailable", "reason": "no session context"}
    assert out["planning"] == {"status": "unavailable", "reason": "no session context"}
    assert "high_confidence_user_underspec" not in out["efficacy"]


def test_both_available_applies_modifier_and_strips_hc():
    out = attach_outcome_axes(
        _craft("A"),
        efficacy=_eff_payload(),
        planning=_plan_payload(),
        mean_kappa=FLOOR_OK,
    )
    assert out["band_raw"] == "A"
    assert out["band"] == "B"
    assert "efficacy" in out["modifier_reason"]
    assert out["efficacy"]["status"] == "available"
    assert out["efficacy"]["attributed_rework_rate"] == 0.5
    assert "high_confidence_user_underspec" not in out["efficacy"]
    assert out["planning"]["status"] == "available"
    assert "high_confidence_underspec" not in out["planning"]
    # craft fields still present flat
    assert out["prompt_id"] == "p-1"
    assert out["percent"] == 91.67


def test_only_efficacy_skips_modifier():
    out = attach_outcome_axes(
        _craft("A"),
        efficacy=_eff_payload(),
        planning=None,
        mean_kappa=FLOOR_OK,
    )
    assert out["band"] == "A"
    assert out["band_raw"] == "A"
    assert out["modifier_reason"] == "no_change"
    assert out["efficacy"]["status"] == "available"
    assert out["planning"]["status"] == "unavailable"


def test_missing_required_efficacy_field_raises():
    bad = _eff_payload()
    del bad["attributed_rework_rate"]
    with pytest.raises(ValueError, match="attributed_rework_rate"):
        attach_outcome_axes(
            _craft("A"),
            efficacy=bad,
            planning=_plan_payload(),
            mean_kappa=FLOOR_OK,
        )


def test_hc_default_false_when_key_absent():
    eff = _eff_payload()
    del eff["high_confidence_user_underspec"]
    plan = _plan_payload(under_specified_initial_plan=2)
    del plan["high_confidence_underspec"]
    out = attach_outcome_axes(
        _craft("A"),
        efficacy=eff,
        planning=plan,
        mean_kappa=FLOOR_OK,
    )
    assert out["band"] == "A"
    assert out["modifier_reason"] == "no_change"


def test_preserves_dataclass_fields_via_asdict():
    report = _craft("B")
    out = attach_outcome_axes(report, efficacy=None, planning=None, mean_kappa=None)
    for key in dataclasses.asdict(report):
        if key == "band":
            continue  # band may stay same here
        assert key in out
