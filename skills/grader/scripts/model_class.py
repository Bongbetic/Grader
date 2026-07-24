"""Heuristic model class classification from a model hint."""
from __future__ import annotations

import re

from domain import TargetModelClass

_REASONING_RE = re.compile(r"o1|o3|codex|reasoning", re.IGNORECASE)


def classify(model_hint: str | None) -> TargetModelClass:
    """Classify a model hint into ``standard``, ``reasoning``, or ``unknown``."""
    if not model_hint:
        return "unknown"
    if _REASONING_RE.search(model_hint):
        return "reasoning"
    return "standard"


def resolve(
    model_hint: str | None,
    *,
    learner_class: TargetModelClass | None = None,
) -> TargetModelClass:
    """Resolve finalize ``--model-class`` from intake hint, else learner pin.

    Intake ``model_hint`` wins when it classifies to ``standard`` or ``reasoning``.
    Cursor and similar adapters often leave ``model_hint=None``; then apply a
    learner-supplied ``standard`` / ``reasoning`` pin so D5 stays assessable.
    When the learner skips, keep ``unknown`` (AS-005: D5 excluded).
    """
    inferred = classify(model_hint)
    if inferred != "unknown":
        return inferred
    if learner_class in ("standard", "reasoning"):
        return learner_class
    return "unknown"
