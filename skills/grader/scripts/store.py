from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import paths

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False

try:
    import msvcrt

    _HAS_MSVCRT = True
except ImportError:
    _HAS_MSVCRT = False


def canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _resolve_root(root: Path | None) -> Path:
    return paths.grader_home() if root is None else root


def _lock_available() -> bool:
    return _HAS_FCNTL or _HAS_MSVCRT


def _lock_exclusive(fh: Any) -> None:
    if _HAS_FCNTL:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)  # type: ignore[arg-type]
    elif _HAS_MSVCRT:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 2**31 - 1)  # type: ignore[attr-defined]


def _unlock(fh: Any) -> None:
    if _HAS_FCNTL:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)  # type: ignore[arg-type]
    elif _HAS_MSVCRT:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 2**31 - 1)  # type: ignore[attr-defined]


def _append_jsonl_locked(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as fh:
        _lock_exclusive(fh)
        try:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            _unlock(fh)


def _append_jsonl_via_temp(path: Path, line: str) -> None:
    existing: list[str] = []
    if path.is_file():
        with path.open("r", encoding="utf-8") as fh:
            existing = fh.readlines()
    tmp = path.parent / f".{path.name}.tmp"
    with tmp.open("w", encoding="utf-8") as fh:
        for existing_line in existing:
            fh.write(existing_line)
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    """Append a single canonical JSON line to path.

    Single-writer assumption: at most one process writes to this file at a
    time. On platforms with file locking (fcntl on Unix, msvcrt on Windows),
    the file is opened exclusively, the line is appended, flushed, and fsynced
    before the lock is released. On platforms without locking or if the lock is
    unavailable, the fallback reads the entire file, writes a new temp copy with
    the appended line, and atomically renames it into place. This is acceptable
    for small JSONL files under the single-writer assumption.
    """
    line = canonical_json(obj) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if _lock_available():
        try:
            _append_jsonl_locked(path, line)
        except OSError:
            _append_jsonl_via_temp(path, line)
    else:
        _append_jsonl_via_temp(path, line)


def atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _as_dict(report: dict[str, Any] | Any) -> dict[str, Any]:
    if isinstance(report, dict):
        return dict(report)
    if dataclasses.is_dataclass(report) and not isinstance(report, type):
        return dataclasses.asdict(report)
    raise TypeError("report must be a dict or dataclass instance")


def save_grade(
    report: dict[str, Any],
    *,
    persist_raw: bool,
    raw_text: str | None,
    excerpt: str,
    root: Path | None = None,
) -> None:
    root = _resolve_root(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "excerpts").mkdir(exist_ok=True)

    record = _as_dict(report)
    if "ingested_at" not in record:
        from datetime import datetime, timezone

        record["ingested_at"] = datetime.now(timezone.utc).isoformat()

    prompt_id = record.get("prompt_id")
    if not prompt_id:
        raise ValueError("report must contain prompt_id")

    atomic_write_text(root / "excerpts" / f"{prompt_id}.txt", excerpt)

    if persist_raw and raw_text is not None:
        (root / "raw").mkdir(exist_ok=True)
        raw_path = root / "raw" / f"{prompt_id}.txt"
        atomic_write_text(raw_path, raw_text)
        record["raw_path"] = str(raw_path.relative_to(root))

    append_jsonl(root / "grades.jsonl", record)


def _last_hash(path: Path) -> str:
    if not path.is_file():
        return "0" * 64
    with path.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()
    if not lines:
        return "0" * 64
    last = json.loads(lines[-1])
    return last.get("hash", "0" * 64)


def append_trend_metric(metric: dict[str, Any], root: Path | None = None) -> None:
    root = _resolve_root(root)
    root.mkdir(parents=True, exist_ok=True)
    metrics_path = root / "metrics.jsonl"

    payload = dict(metric)
    prev_hash = _last_hash(metrics_path)
    canonical = canonical_json(payload)
    digest = hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()
    payload["prev_hash"] = prev_hash
    payload["hash"] = digest

    append_jsonl(metrics_path, payload)


def load_jsonl_line(line: str) -> dict[str, Any]:
    return json.loads(line)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def save_turns(records, *, persist_transcripts: bool, root: Path | None = None) -> dict[str, Any]:
    """Persist redacted TurnRecords, or compute nothing-to-disk in no-persist mode.

    In no-persist mode returns session ids for in-memory analysis without
    writing any transcript text. When persisting, only redacted fields are
    stored (no raw prompt text ever).
    """
    session_ids: list[str] = []
    for rec in records:
        if rec.session_id not in session_ids:
            session_ids.append(rec.session_id)
    if not persist_transcripts:
        return {"persisted": 0, "session_ids": session_ids}

    root = _resolve_root(root)
    path = root / "transcripts.jsonl"
    persisted = 0
    for rec in records:
        append_jsonl(path, {
            "source_tool": rec.source_tool,
            "session_id": rec.session_id,
            "turn_index": rec.turn_index,
            "role": rec.role,
            "timestamp": rec.timestamp,
            "text_redacted": rec.text_redacted,
            "workflow_marker": rec.workflow_marker,
            "analysis_eligible": rec.analysis_eligible,
        })
        persisted += 1
    return {"persisted": persisted, "session_ids": session_ids}
