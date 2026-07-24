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
