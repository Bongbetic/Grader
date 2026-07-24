from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import paths
from curriculum import add_auto_exemplar
from store import append_jsonl

try:
    import trends

    _HAS_TRENDS = True
except ImportError:
    _HAS_TRENDS = False

REQUIRED_FIELDS = {
    "id",
    "prompt_id",
    "dimension_id",
    "learner_prompt",
    "grade_report",
    "coaching_notes",
}


def _load_config(root: Path) -> dict[str, Any]:
    config_path = root / "config.json"
    if not config_path.is_file():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _to_dict(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _to_dict(dataclasses.asdict(obj))
    return obj


def record(session: dict[str, Any], *, root: Path | None = None) -> Path:
    """Append a PracticeSession to ~/.grader/practice.jsonl.

    If the session contains an ``exemplar`` dict and the grader store config
    has ``auto_exemplar_opt_in: true``, the exemplar is saved to the
    curriculum auto exemplar directory via ``curriculum.add_auto_exemplar``.
    """
    root = paths.grader_home() if root is None else root
    root.mkdir(parents=True, exist_ok=True)

    missing = REQUIRED_FIELDS - set(session.keys())
    if missing:
        raise ValueError(
            f"practice session missing required fields: {', '.join(sorted(missing))}"
        )

    record = _to_dict(session)
    if "recorded_at" not in record:
        record["recorded_at"] = datetime.now(timezone.utc).isoformat()

    practice_path = root / "practice.jsonl"
    append_jsonl(practice_path, record)

    exemplar = session.get("exemplar")
    config = _load_config(root)
    if exemplar is not None and config.get("auto_exemplar_opt_in") is True:
        add_auto_exemplar(exemplar)

    return practice_path


def pick_practice_dimension(*, root: Path | None = None) -> str:
    """Return the weakest failing dimension from trends if available, else D1."""
    if _HAS_TRENDS:
        try:
            dim = trends.most_frequent_failing(root=root)
            if dim:
                return dim
        except Exception:
            pass
    return "D1"
