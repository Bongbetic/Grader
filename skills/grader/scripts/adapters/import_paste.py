"""Import and paste adapters for free-form prompt text."""
from __future__ import annotations

from adapters import _process_learner_text


def from_text(text: str, *, source: str = "paste") -> list[dict]:
    """Return a single raw candidate from pasted or imported text."""
    assert source in ("import", "paste")
    cleaned, notes = _process_learner_text(text)
    if not cleaned:
        return []
    return [
        {
            "text": cleaned,
            "timestamp": "",
            "source_tool": source,
            "model_hint": None,
            "_redaction_notes": notes,
        }
    ]
