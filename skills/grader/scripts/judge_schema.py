from __future__ import annotations

import uuid
from typing import Any

from domain import DIMENSION_WEIGHTS, NA, DimensionScore, GradeReport, TargetModelClass
from redact import redact_text
from score_math import finalize

REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11"
)


def parse_judge_output(data: dict[str, Any]) -> tuple[list[DimensionScore], dict[str, str], list[str]]:
    """Validate judge JSON and return dimension scores, rationales, and disqualifier flags.

    The host model may supply percent/band values, but they are ignored here.
    All D1-D11 dimensions must be present with a level of 0-3 or N/A.
    """
    if not isinstance(data, dict):
        raise ValueError("judge output must be a JSON object")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("judge output must contain a 'dimensions' object")

    missing = [d for d in REQUIRED_DIMENSIONS if d not in dimensions]
    if missing:
        raise ValueError(f"missing dimensions: {', '.join(missing)}")

    unknown = [d for d in dimensions if d not in REQUIRED_DIMENSIONS]
    if unknown:
        raise ValueError(f"unknown dimensions: {', '.join(unknown)}")

    scores: list[DimensionScore] = []
    rationales: dict[str, str] = {}

    for dim in REQUIRED_DIMENSIONS:
        entry = dimensions[dim]
        if not isinstance(entry, dict):
            raise ValueError(f"dimension {dim} must be an object")

        level = entry.get("level")
        if level is None:
            raise ValueError(f"dimension {dim} missing level")
        if level != NA and level not in (0, 1, 2, 3):
            raise ValueError(f"dimension {dim} level must be 0-3 or N/A")

        scores.append(DimensionScore(dim, level, DIMENSION_WEIGHTS[dim]))

        rationale = entry.get("rationale")
        if rationale is not None:
            if not isinstance(rationale, str):
                raise ValueError(f"dimension {dim} rationale must be a string")
            rationales[dim] = rationale

    disqualifiers = data.get("disqualifiers", [])
    if not isinstance(disqualifiers, list):
        raise ValueError("disqualifiers must be a list")

    flags = [str(f) for f in disqualifiers]
    return scores, rationales, flags


def build_grade_report(
    prompt_id: str,
    scores: list[DimensionScore],
    rationales: dict[str, str],
    flags: list[str],
    model_class: TargetModelClass,
) -> GradeReport:
    """Compute a final GradeReport from parsed judge output.

    Percent and band are always recomputed by score_math.finalize. Rationales
    are redacted before storage.
    """
    earned, possible, percent, band, caps_applied = finalize(
        scores,
        disqualifier_flags=flags,
        target_model_class=model_class,
    )

    redacted_rationales: dict[str, str] = {}
    for dim, text in rationales.items():
        redacted, _notes = redact_text(text)
        redacted_rationales[dim] = redacted

    return GradeReport(
        id=uuid.uuid4().hex,
        prompt_id=prompt_id,
        dimension_scores=scores,
        earned=earned,
        possible=possible,
        percent=percent,
        band=band,
        caps_applied=caps_applied,
        rationales=redacted_rationales,
    )
