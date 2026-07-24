from calibration_gate import calibration_gate_ok, AGREEMENT_FLOOR


def test_uncalibrated_gate_closed():
    assert calibration_gate_ok(None) is False


def test_below_floor_closed():
    assert calibration_gate_ok(AGREEMENT_FLOOR - 0.01) is False


def test_at_or_above_floor_open():
    assert calibration_gate_ok(AGREEMENT_FLOOR) is True
    assert calibration_gate_ok(0.9) is True
