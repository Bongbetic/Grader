DNA_DIMENSIONS = [
    "clarity",
    "context",
    "success_criteria",
    "structure",
    "constraints",
    "examples",
    "agentic_hygiene",
    "cross_session_consistency",
]

REQUIRED_KEYS = [
    "meta",
    "dna",
    "scores",
    "efficiency",
    "habits",
    "learning_cards",
    "practice_pack",
    "live_assessment",
    "overall_letter",
]


def empty_profile(flow: str, meta: dict | None = None) -> dict:
    base_meta = {
        "flow": flow,
        "intake_path": None,
        "prompts_sampled": 0,
        "prompts_available": 0,
        "sessions_scanned": 0,
    }
    if meta:
        base_meta.update(meta)
        base_meta["flow"] = flow

    return {
        "meta": base_meta,
        "dna": [
            {"id": dimension, "label": dimension, "score": None, "verdict": None, "evidence": []}
            for dimension in DNA_DIMENSIONS
        ],
        "scores": {"skill": None, "efficiency": None, "consistency": None, "planning": None},
        "efficiency": {},
        "habits": [],
        "learning_cards": [],
        "practice_pack": [],
        "live_assessment": None,
        "overall_letter": None,
    }


def validate_profile_keys(profile: dict) -> list[str]:
    return [key for key in REQUIRED_KEYS if key not in profile]
