from __future__ import annotations

import json
from pathlib import Path

_LESSONS_DIR = Path(__file__).resolve().parents[1] / "curriculum" / "lessons"
_EXEMPLARS_DIR = Path(__file__).resolve().parents[1] / "curriculum" / "exemplars"


def list_lessons() -> list[str]:
    """Return lesson ids (markdown file stems)."""
    if not _LESSONS_DIR.exists():
        return []
    return sorted(p.stem for p in _LESSONS_DIR.glob("*.md"))


def load_lesson(lesson_id: str) -> str:
    """Return the markdown content of a lesson."""
    path = _LESSONS_DIR / f"{lesson_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"lesson not found: {lesson_id}")
    return path.read_text(encoding="utf-8")


def _load_exemplars_in_dir(origin: str, directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    exemplars: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if "origin" not in data:
            data = {**data, "origin": origin}
        exemplars.append(data)
    return exemplars


def list_exemplars() -> list[dict]:
    """Return all seed and auto-built exemplars."""
    return [
        *_load_exemplars_in_dir("seed", _EXEMPLARS_DIR / "seed"),
        *_load_exemplars_in_dir("auto-built", _EXEMPLARS_DIR / "auto"),
    ]


def add_auto_exemplar(data: dict) -> dict:
    """Save an auto-built exemplar and return it with origin set.

    Raises ValueError if the data does not contain an ``id``.
    """
    if not data.get("id"):
        raise ValueError("auto exemplar must have an id")
    auto_dir = _EXEMPLARS_DIR / "auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    record = {**data, "origin": "auto-built"}
    out_path = auto_dir / f"{record['id']}.json"
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record
