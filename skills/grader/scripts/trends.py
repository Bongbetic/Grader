from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import paths
import store

DIMENSION_IDS = (
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11"
)
_AB_BANDS = frozenset({"A", "B"})


def _parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _date_from_record(record: dict[str, Any]) -> datetime.date | None:
    dt = _parse_time(
        record.get("ingested_at")
        or record.get("graded_at")
        or record.get("timestamp")
        or record.get("recorded_at")
        or record.get("period")
    )
    return dt.date() if dt else None


def _levels_from_grade(record: dict[str, Any]) -> dict[str, int]:
    levels: dict[str, int] = {}
    for score in record.get("dimension_scores", []):
        if not isinstance(score, dict):
            continue
        dim = score.get("dimension_id")
        level = score.get("level")
        if dim is None or level is None or isinstance(level, str):
            continue
        try:
            levels[dim] = int(level)
        except (TypeError, ValueError):
            continue
    return levels


def _levels_from_metric(record: dict[str, Any]) -> dict[str, int]:
    levels: dict[str, int] = {}
    raw = record.get("dimension_levels", {})
    if not isinstance(raw, dict):
        return levels
    for dim, level in raw.items():
        if level is None or isinstance(level, str):
            continue
        try:
            levels[dim] = int(level)
        except (TypeError, ValueError):
            continue
    return levels


def _normalize_records(root: Path) -> list[dict[str, Any]]:
    """Load grades and metrics, returning chronologically sorted trend records.

    Grade records are preferred when a metric exists for the same prompt_id,
    avoiding double-counting from the finalize_grade metric that mirrors each
    grade.
    """
    records: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()

    grades_path = root / "grades.jsonl"
    for record in store.load_jsonl(grades_path):
        t = _parse_time(
            record.get("ingested_at")
            or record.get("graded_at")
            or record.get("timestamp")
        )
        if t is None:
            continue
        prompt_id = record.get("prompt_id")
        if prompt_id:
            seen_prompts.add(prompt_id)
        records.append({
            "t": t,
            "band": record.get("band"),
            "levels": _levels_from_grade(record),
        })

    metrics_path = root / "metrics.jsonl"
    for record in store.load_jsonl(metrics_path):
        t = _parse_time(
            record.get("ingested_at")
            or record.get("timestamp")
            or record.get("period")
        )
        if t is None:
            continue
        prompt_id = record.get("prompt_id")
        if prompt_id and prompt_id in seen_prompts:
            continue
        records.append({
            "t": t,
            "band": record.get("band"),
            "levels": _levels_from_metric(record),
        })

    records.sort(key=lambda r: r["t"])
    return records


def _is_available(root: Path) -> bool:
    grades_path = root / "grades.jsonl"
    grade_count = 0
    for record in store.load_jsonl(grades_path):
        if _parse_time(
            record.get("ingested_at")
            or record.get("graded_at")
            or record.get("timestamp")
        ) is not None:
            grade_count += 1
    if grade_count >= 2:
        return True

    metric_dates = {
        d
        for record in store.load_jsonl(root / "metrics.jsonl")
        if (d := _date_from_record(record)) is not None
    }
    return len(metric_dates) >= 2


def _resolve_root(root: Path | None) -> Path:
    return paths.grader_home() if root is None else root


def outcome_metric_fields(efficacy=None, planning=None) -> dict[str, Any]:
    """Optional outcome fields for trend payloads."""
    return {
        "attributed_rework_rate": efficacy.attributed_rework_rate if efficacy else None,
        "under_specified_initial_plan": planning.under_specified_initial_plan if planning else None,
    }


def compute_trends(root: Path | None = None) -> dict[str, Any]:
    """Aggregate trends from grades and persistent metrics.

    Returns:
        {
            "available": bool,
            "dimension_levels": {D1: [{t, level}, ...], ...},
            "bands_over_time": [{t, band}, ...],
            "most_frequent_failing": {dimension_id, count} | None,
            "streaks": {
                "consecutive_ab_bands": int,
                "consecutive_practice_days": int,
            },
        }

    Trends are available when there are at least two grade records or metrics
    cover at least two distinct periods.
    """
    root = _resolve_root(root)
    records = _normalize_records(root)

    available = _is_available(root)

    if not available:
        return {
            "available": False,
            "dimension_levels": {},
            "bands_over_time": [],
            "most_frequent_failing": None,
            "streaks": {
                "consecutive_ab_bands": 0,
                "consecutive_practice_days": 0,
            },
        }

    dimension_levels: dict[str, list[dict[str, Any]]] = {
        dim: [] for dim in DIMENSION_IDS
    }
    bands_over_time: list[dict[str, Any]] = []
    failing_counts: Counter = Counter()

    for rec in records:
        iso_t = rec["t"].isoformat()
        band = rec.get("band")
        if band:
            bands_over_time.append({"t": iso_t, "band": band})
        for dim, level in rec["levels"].items():
            if dim not in dimension_levels:
                continue
            dimension_levels[dim].append({"t": iso_t, "level": level})
            if level < 3:
                failing_counts[dim] += 1

    dimension_levels = {dim: pts for dim, pts in dimension_levels.items() if pts}

    most_frequent = None
    if failing_counts:
        top_dim, top_count = sorted(
            failing_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0]
        most_frequent = {
            "dimension_id": top_dim,
            "count": top_count,
        }

    streaks = {
        "consecutive_ab_bands": _consecutive_ab_bands(records),
        "consecutive_practice_days": _consecutive_practice_days(root),
    }

    return {
        "available": True,
        "dimension_levels": dimension_levels,
        "bands_over_time": bands_over_time,
        "most_frequent_failing": most_frequent,
        "streaks": streaks,
    }


def most_frequent_failing(root: Path | None = None) -> str | None:
    """Return the dimension_id most often graded below level 3, if any."""
    trends = compute_trends(root=root)
    mf = trends.get("most_frequent_failing")
    if mf is None:
        return None
    return str(mf["dimension_id"])


def _consecutive_ab_bands(records: list[dict[str, Any]]) -> int:
    sorted_desc = sorted(records, key=lambda r: r["t"], reverse=True)
    count = 0
    for rec in sorted_desc:
        if rec.get("band") in _AB_BANDS:
            count += 1
        else:
            break
    return count


def _consecutive_practice_days(root: Path) -> int:
    practice_path = root / "practice.jsonl"
    dates: set[datetime.date] = set()
    for record in store.load_jsonl(practice_path):
        d = _date_from_record(record)
        if d is not None:
            dates.add(d)
    if not dates:
        return 0
    sorted_dates = sorted(dates, reverse=True)
    streak = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i - 1] - timedelta(days=1):
            streak += 1
        else:
            break
    return streak
