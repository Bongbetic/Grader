from profile_schema import empty_profile


def test_scores_has_planning_slot():
    profile = empty_profile("grade")
    assert "planning" in profile["scores"]
    assert profile["scores"]["planning"] is None
    # existing keys preserved
    assert set(profile["scores"]) == {"skill", "efficiency", "consistency", "planning"}
