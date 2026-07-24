"""Import and paste adapters for free-form prompt text."""
from __future__ import annotations


def from_text(text: str, *, source: str = "paste") -> list[dict]:
    """Return a single raw candidate from pasted or imported text."""
    assert source in ("import", "paste")
    return [
        {
            "text": text,
            "timestamp": "",
            "source_tool": source,
            "model_hint": None,
        }
    ]
