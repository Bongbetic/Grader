from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import paths
import store


_ALLOWED_PURGE = frozenset({"raw", "excerpts", "metrics", "consent", "transcripts", "all"})


def _resolve_root(root: Path | None) -> Path:
    return paths.grader_home() if root is None else root


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _is_expired(record: dict[str, Any], now: datetime, days: int) -> bool:
    ingested_at = record.get("ingested_at")
    if not ingested_at:
        return False
    try:
        dt = _parse_iso(str(ingested_at))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).days > days


_RAW_FIELD_KEYS = {"raw_path", "raw_text", "persist_raw"}


def _strip_raw_fields(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in _RAW_FIELD_KEYS}


def purge_expired(root: Path | None = None, *, now: Any = None, days: int = 30) -> int:
    root = _resolve_root(root)
    grades_path = root / "grades.jsonl"
    if not grades_path.is_file():
        return 0

    now = now if now is not None else datetime.now(timezone.utc)
    if isinstance(now, str):
        now = _parse_iso(now)

    with grades_path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()

    expired_count = 0
    kept: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if _is_expired(record, now, days):
            expired_count += 1
            prompt_id = record.get("prompt_id")
            if prompt_id:
                raw_file = root / "raw" / f"{prompt_id}.txt"
                excerpt_file = root / "excerpts" / f"{prompt_id}.txt"
                try:
                    raw_file.unlink()
                except FileNotFoundError:
                    pass
                try:
                    excerpt_file.unlink()
                except FileNotFoundError:
                    pass
            record = _strip_raw_fields(record)
        kept.append(record)

    fd, tmp_path = tempfile.mkstemp(dir=root, prefix=".grades.jsonl", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for record in kept:
                fh.write(store.canonical_json(record) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, grades_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise

    return expired_count


def _collect_prompt_ids(directory: Path) -> set[str]:
    ids: set[str] = set()
    if directory.is_dir():
        for item in directory.iterdir():
            if item.is_file():
                ids.add(item.stem)
    return ids


def user_purge(root: Path | None = None, *, what: set[str]) -> None:
    root = _resolve_root(root)
    if not what.issubset(_ALLOWED_PURGE):
        raise ValueError(f"what must be subset of {_ALLOWED_PURGE}")

    if "all" in what:
        what = {"raw", "excerpts", "metrics", "consent", "grades", "transcripts"}

    purged_ids: set[str] = set()
    if "raw" in what:
        purged_ids.update(_collect_prompt_ids(root / "raw"))
    if "excerpts" in what:
        purged_ids.update(_collect_prompt_ids(root / "excerpts"))

    if "raw" in what:
        shutil.rmtree(root / "raw", ignore_errors=True)
    if "excerpts" in what:
        shutil.rmtree(root / "excerpts", ignore_errors=True)
    if "metrics" in what:
        try:
            (root / "metrics.jsonl").unlink()
        except FileNotFoundError:
            pass
    if "consent" in what:
        try:
            (root / "consent.json").unlink()
        except FileNotFoundError:
            pass
    if "grades" in what:
        try:
            (root / "grades.jsonl").unlink()
        except FileNotFoundError:
            pass
    if "transcripts" in what:
        try:
            (root / "transcripts.jsonl").unlink()
        except FileNotFoundError:
            pass
    if "grades" not in what and purged_ids:
        grades_path = root / "grades.jsonl"
        if grades_path.is_file():
            records = store.load_jsonl(grades_path)
            rewritten: list[dict[str, Any]] = []
            for record in records:
                if record.get("prompt_id") in purged_ids:
                    record = _strip_raw_fields(record)
                rewritten.append(record)
            tmp = root / ".grades.jsonl.tmp"
            with tmp.open("w", encoding="utf-8") as fh:
                for record in rewritten:
                    fh.write(store.canonical_json(record) + "\n")
                    fh.flush()
                os.fsync(fh.fileno())
            tmp.replace(grades_path)


_CATEGORY_FILES = {
    "metrics": "metrics.jsonl",
    "consent": "consent.json",
    "grades": "grades.jsonl",
    "transcripts": "transcripts.jsonl",
}
_CATEGORY_DIRS = {"raw": "raw", "excerpts": "excerpts"}


def verify_purged(root: Path | None = None, *, categories: set[str]) -> dict[str, bool]:
    """Return per-category True iff no residual file/dir remains for it."""
    root = _resolve_root(root)
    result: dict[str, bool] = {}
    for cat in categories:
        if cat in _CATEGORY_FILES:
            result[cat] = not (root / _CATEGORY_FILES[cat]).exists()
        elif cat in _CATEGORY_DIRS:
            d = root / _CATEGORY_DIRS[cat]
            result[cat] = (not d.exists()) or not any(d.iterdir())
        else:
            result[cat] = True
    return result
