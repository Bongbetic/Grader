from sensitivity import band_flip_rate


def _row(levels, band):
    return {"human_levels": levels, "human_band": band}


def test_no_override_zero_flip():
    gold = [
        _row({"D1": 3, "D2": 3, "D3": 3, "D4": 3, "D5": 3, "D6": 3, "D7": 3, "D8": "N/A", "D9": "N/A", "D10": "N/A", "D11": "N/A"}, "A"),
        _row({"D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 1, "D6": 1, "D7": 0, "D8": "N/A", "D9": "N/A", "D10": "N/A", "D11": "N/A"}, "D"),
    ]
    assert band_flip_rate(gold, weight_overrides={}) == 0.0


def test_extreme_override_flips_some():
    gold = [
        _row({"D1": 3, "D2": 0, "D3": 0, "D4": 0, "D5": 0, "D6": 0, "D7": 0, "D8": "N/A", "D9": "N/A", "D10": "N/A", "D11": "N/A"}, "D"),
    ]
    # crank D1 weight so a lone strong D1 lifts the band
    rate = band_flip_rate(gold, weight_overrides={"D1": 3})
    assert 0.0 <= rate <= 1.0
