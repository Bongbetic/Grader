from calibration_report import dimension_agreement


def test_perfect_judge_scores_high():
    gold = [
        {"id": "a", "human_levels": {"D1": 3, "D2": 2, "D3": 1, "D4": 0, "D5": 2, "D6": 3, "D7": 2, "D8": "N/A", "D9": "N/A", "D10": "N/A", "D11": "N/A"}},
        {"id": "b", "human_levels": {"D1": 0, "D2": 1, "D3": 2, "D4": 3, "D5": 1, "D6": 2, "D7": 1, "D8": "N/A", "D9": "N/A", "D10": "N/A", "D11": "N/A"}},
    ]
    judge = {r["id"]: dict(r["human_levels"]) for r in gold}
    result = dimension_agreement(gold, judge)
    assert result["D1"] == 1.0
    assert result["_mean"] > 0.99


def test_na_dimensions_excluded():
    gold = [{"id": "a", "human_levels": {f"D{i}": ("N/A" if i > 7 else 2) for i in range(1, 12)}}]
    judge = {"a": dict(gold[0]["human_levels"])}
    result = dimension_agreement(gold, judge)
    # D8-D11 all N/A -> excluded -> not in result
    assert "D8" not in result
    assert "D1" in result
