from finalize_grade import confidence_label


def test_confidence_bands():
    assert confidence_label(None) == "uncalibrated"
    assert confidence_label(0.5) == "low"
    assert confidence_label(0.6) == "medium"
    assert confidence_label(0.75) == "high"
    assert confidence_label(0.95) == "high"
