from profile_schema import DNA_DIMENSIONS, empty_profile, validate_profile_keys


def test_empty_profile_has_required_keys_and_eight_dna_slots():
    p = empty_profile("grade", meta={"intake_path": "auto", "prompts_sampled": 0})
    assert validate_profile_keys(p) == []
    assert p["meta"]["flow"] == "grade"
    assert len(DNA_DIMENSIONS) == 8
    assert len(p["dna"]) == 8
    assert p["scores"] == {"skill": None, "efficiency": None, "consistency": None}
    assert p["overall_letter"] is None
