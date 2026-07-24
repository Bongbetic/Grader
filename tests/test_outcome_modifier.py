from domain import EfficacyReport, PlanningReport
from score_math import apply_outcome_modifier

FLOOR_OK = 0.7  # above AGREEMENT_FLOOR


def _eff(rate=0.5, worst=4):
    return EfficacyReport("s1", 2.0, 0.3, rate, worst, 2, 1, False)


def _plan(underspec=0):
    return PlanningReport("s1", 0, 0, 0, 0, underspec)


def test_gate_closed_no_change():
    band, reason = apply_outcome_modifier(
        "A", efficacy=_eff(), planning=_plan(),
        efficacy_high_confidence_user_underspec=True,
        planning_high_confidence_underspec=False,
        mean_kappa=None,  # uncalibrated -> gate closed
    )
    assert band == "A"
    assert reason == "no_change"


def test_high_conf_user_underspec_lowers_one_letter():
    band, reason = apply_outcome_modifier(
        "A", efficacy=_eff(rate=0.5), planning=_plan(),
        efficacy_high_confidence_user_underspec=True,
        planning_high_confidence_underspec=False,
        mean_kappa=FLOOR_OK,
    )
    assert band == "B"
    assert "efficacy" in reason


def test_both_signals_still_one_letter():
    band, _ = apply_outcome_modifier(
        "A", efficacy=_eff(rate=0.9), planning=_plan(underspec=2),
        efficacy_high_confidence_user_underspec=True,
        planning_high_confidence_underspec=True,
        mean_kappa=FLOOR_OK,
    )
    assert band == "B"  # not C — combined cap is one letter


def test_low_confidence_never_moves():
    band, reason = apply_outcome_modifier(
        "A", efficacy=_eff(rate=0.9), planning=_plan(),
        efficacy_high_confidence_user_underspec=False,
        planning_high_confidence_underspec=False,
        mean_kappa=FLOOR_OK,
    )
    assert band == "A"
    assert reason == "no_change"


def test_c_never_becomes_d():
    band, _ = apply_outcome_modifier(
        "C", efficacy=_eff(rate=0.9), planning=_plan(),
        efficacy_high_confidence_user_underspec=True,
        planning_high_confidence_underspec=False,
        mean_kappa=FLOOR_OK,
    )
    assert band == "C"  # signals alone never push to D


def test_d_band_unchanged():
    band, reason = apply_outcome_modifier(
        "D", efficacy=_eff(), planning=_plan(),
        efficacy_high_confidence_user_underspec=True,
        planning_high_confidence_underspec=False,
        mean_kappa=FLOOR_OK,
    )
    assert band == "D"
    assert reason == "no_change"
