from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import paths
import store


def _resolve_root(root: Path | None = None) -> Path:
    return paths.grader_home() if root is None else root


def _load_consent(root: Path) -> dict[str, Any]:
    path = root / "consent.json"
    if not path.is_file():
        return {"grants": {}}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def has_consent(tool: str, root: Path | None = None) -> bool:
    root = _resolve_root(root)
    data = _load_consent(root)
    return tool in data.get("grants", {})


def grant_consent(tool: str, root: Path | None = None) -> None:
    root = _resolve_root(root)
    root.mkdir(parents=True, exist_ok=True)
    data = _load_consent(root)
    data["grants"][tool] = datetime.now(timezone.utc).isoformat()
    path = root / "consent.json"
    store.atomic_write_json(path, data)


def has_transcript_consent(root: Path | None = None) -> bool:
    root = _resolve_root(root)
    data = _load_consent(root)
    return bool(data.get("transcript_analysis"))


def grant_transcript_consent(root: Path | None = None) -> None:
    root = _resolve_root(root)
    root.mkdir(parents=True, exist_ok=True)
    data = _load_consent(root)
    data["transcript_analysis"] = datetime.now(timezone.utc).isoformat()
    path = root / "consent.json"
    store.atomic_write_json(path, data)
