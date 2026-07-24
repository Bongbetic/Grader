"""Compose many finalized per-prompt grade reports into one session rollup."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from domain import DIMENSION_WEIGHTS
from score_math import band_from_percent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_CONFIDENCE_RANK = {
    "uncalibrated": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}
_SEVERITY_RANK = {
    "none": 0,
    "clear": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
_BAND_ORDER = ("A", "B", "C", "D")
_PLANNING_COUNTERS: tuple[str, ...] = (
    "planned_decomposition",
    "under_specified_initial_plan",
    "scope_change_without_prior_signal",
    "additive_feature",
    "adaptive_change_with_evidence",
)
_STRONG_CAP = 120
_WEAK_CAP = 120


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _round1(value: float) -> float:
    return round(value, 1)


def _prompt_id(report: dict[str, Any]) -> str:
    return str(report.get("prompt_id") or report.get("id") or "unknown")


def _slot_text(slots: dict[str, Any] | None, key: str) -> str | None:
    if not slots:
        return None
    value = slots.get(key)
    if isinstance(value, dict):
        text = value.get("text")
        return str(text) if text else None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _truncate(text: str, cap: int) -> str:
    return text if len(text) <= cap else text[:cap]


def _behavior_mix(reports: list[dict[str, Any]]) -> str:
    bands = Counter(str(r.get("band") or "?") for r in reports)
    parts = [f"{b}×{bands[b]}" for b in _BAND_ORDER if bands.get(b)]
    extras = sorted(k for k in bands if k not in _BAND_ORDER)
    parts.extend(f"{k}×{bands[k]}" for k in extras)
    class_counts = Counter(
        str((r.get("classification_summary") or {}).get("prompt_class"))
        for r in reports
        if isinstance(r.get("classification_summary"), dict)
        and (r.get("classification_summary") or {}).get("prompt_class")
    )
    if class_counts:
        class_parts = [
            f"{name}×{count}" for name, count in sorted(class_counts.items())
        ]
        return f"bands { ' · '.join(parts) }; classes { ' · '.join(class_parts) }"
    return f"bands { ' · '.join(parts) }"


def _intake_strip(
    reports: list[dict[str, Any]], intake: dict[str, Any] | None
) -> dict[str, Any]:
    intake = dict(intake or {})
    tools = intake.get("tools")
    if not tools:
        tools = sorted(
            {
                str(r.get("source_tool"))
                for r in reports
                if r.get("source_tool")
            }
        )
    if isinstance(tools, str):
        tools = [tools]
    out: dict[str, Any] = {
        "prompt_count": len(reports),
        "tools": list(tools),
        "intake_path": intake.get("intake_path") or "unknown",
    }
    if intake.get("window_start"):
        out["window_start"] = intake["window_start"]
    if intake.get("window_end"):
        out["window_end"] = intake["window_end"]
    if intake.get("session_id"):
        out["session_id"] = intake["session_id"]
    return out


def _worst_confidence(reports: list[dict[str, Any]]) -> str:
    worst = "high"
    worst_rank = _CONFIDENCE_RANK["high"]
    for report in reports:
        label = str(report.get("confidence") or "uncalibrated")
        rank = _CONFIDENCE_RANK.get(label, _CONFIDENCE_RANK["uncalibrated"])
        if rank < worst_rank:
            worst = label
            worst_rank = rank
    return worst


def _union_caps(reports: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for report in reports:
        for cap in report.get("caps_applied") or []:
            text = str(cap)
            if text not in seen:
                seen.add(text)
                out.append(text)
    return sorted(out)


def _mean_dimensions(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    levels: dict[str, list[int]] = {dim: [] for dim in DIMENSION_WEIGHTS}
    for report in reports:
        for score in report.get("dimension_scores") or []:
            dim = str(score.get("dimension_id") or "")
            if dim not in levels:
                continue
            level = score.get("level")
            if level in (None, "N/A", "n/a"):
                continue
            levels[dim].append(int(level))
    out: list[dict[str, Any]] = []
    for dim, weight in DIMENSION_WEIGHTS.items():
        vals = levels[dim]
        if not vals:
            level: int | str = "N/A"
        else:
            level = int(round(_mean([float(v) for v in vals])))
        out.append({"dimension_id": dim, "level": level, "weight": weight})
    return out


def _dimension_rationales(reports: list[dict[str, Any]]) -> dict[str, str]:
    n = len(reports)
    return {
        dim: f"rollup mean across {n} prompts"
        for dim, scores in (
            (
                dim,
                [
                    s
                    for r in reports
                    for s in (r.get("dimension_scores") or [])
                    if s.get("dimension_id") == dim
                    and s.get("level") not in (None, "N/A", "n/a")
                ],
            )
            for dim in DIMENSION_WEIGHTS
        )
        if scores
    }


def _aggregate_efficacy(reports: list[dict[str, Any]]) -> dict[str, Any]:
    available = [
        r["efficacy"]
        for r in reports
        if isinstance(r.get("efficacy"), dict)
        and r["efficacy"].get("status") == "available"
    ]
    if not available:
        return {"status": "unavailable", "reason": "no session context"}
    session_ids = [e.get("session_id") for e in available if e.get("session_id")]
    return {
        "status": "available",
        "session_id": session_ids[0] if session_ids else "rollup",
        "prompts_per_task_mean": _round1(
            _mean([float(e.get("prompts_per_task_mean") or 0) for e in available])
        ),
        "single_shot_rate": _round1(
            _mean([float(e.get("single_shot_rate") or 0) for e in available])
        ),
        "attributed_rework_rate": _round1(
            _mean([float(e.get("attributed_rework_rate") or 0) for e in available])
        ),
        "worst_task_prompt_count": max(
            int(e.get("worst_task_prompt_count") or 0) for e in available
        ),
        "restates": sum(int(e.get("restates") or 0) for e in available),
        "corrections": sum(int(e.get("corrections") or 0) for e in available),
        "abandoned_goal": any(bool(e.get("abandoned_goal")) for e in available),
    }


def _aggregate_planning(reports: list[dict[str, Any]]) -> dict[str, Any]:
    available = [
        r["planning"]
        for r in reports
        if isinstance(r.get("planning"), dict)
        and r["planning"].get("status") == "available"
    ]
    if not available:
        return {"status": "unavailable", "reason": "no session context"}
    session_ids = [p.get("session_id") for p in available if p.get("session_id")]
    out: dict[str, Any] = {
        "status": "available",
        "session_id": session_ids[0] if session_ids else "rollup",
    }
    for key in _PLANNING_COUNTERS:
        out[key] = sum(int(p.get(key) or 0) for p in available)
    return out


def _aggregate_security(reports: list[dict[str, Any]]) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for report in reports:
        security = report.get("security")
        if not isinstance(security, dict):
            continue
        status = security.get("status")
        if status in (None, "none", "clear"):
            continue
        hits.append(security)
    if not hits:
        return {"status": "none"}
    worst = max(
        hits,
        key=lambda s: _SEVERITY_RANK.get(str(s.get("severity") or "low"), 1),
    )
    n = len(reports)
    return {
        "status": "hit",
        "severity": worst.get("severity") or "low",
        "summary": f"{len(hits)} of {n} prompts with residual secret hits",
        "action": worst.get("action")
        or "Rotate referenced credentials; never paste live keys — point at env.",
    }


def _modal_classification(reports: list[dict[str, Any]]) -> dict[str, Any] | None:
    classes: list[str] = []
    complexities: list[str] = []
    causes: list[str] = []
    for report in reports:
        summary = report.get("classification_summary")
        if not isinstance(summary, dict):
            continue
        if summary.get("prompt_class"):
            classes.append(str(summary["prompt_class"]))
        if summary.get("task_complexity"):
            complexities.append(str(summary["task_complexity"]))
        if summary.get("rework_cause"):
            causes.append(str(summary["rework_cause"]))
    if not (classes or complexities or causes):
        return None
    out: dict[str, Any] = {}
    if classes:
        out["prompt_class"] = Counter(classes).most_common(1)[0][0]
    if complexities:
        out["task_complexity"] = Counter(complexities).most_common(1)[0][0]
    if causes:
        out["rework_cause"] = Counter(causes).most_common(1)[0][0]
    return out


def _exemplar_slots(reports: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        reports,
        key=lambda r: (-float(r.get("percent") or 0.0), _prompt_id(r)),
    )
    best = ranked[0]
    worst = ranked[-1]

    def pick(report: dict[str, Any], key: str, cap: int) -> str:
        text = _slot_text(
            report.get("slots") if isinstance(report.get("slots"), dict) else None,
            key,
        )
        if not text:
            excerpt = report.get("excerpt") or ""
            text = f"{_prompt_id(report)}: {excerpt}".strip()
        else:
            text = f"{_prompt_id(report)}: {text}"
        return _truncate(text, cap)

    return {
        "strongest": pick(best, "strongest", _STRONG_CAP),
        "weakest": pick(worst, "weakest", _WEAK_CAP),
        "next_actions": [],
    }


def _modifier_reason(reports: list[dict[str, Any]]) -> str:
    changed = [
        str(r.get("modifier_reason"))
        for r in reports
        if r.get("modifier_reason") not in (None, "no_change")
    ]
    if not changed:
        return f"rollup:{len(reports)} prompts"
    return f"rollup:{len(reports)} prompts; {len(changed)} modified"


def load_reports_manifest(manifest_path: Path) -> list[Path]:
    """Load report file paths from a JSON manifest (array of path strings)."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"manifest file not found: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("manifest must be a JSON array of report paths")
    paths: list[Path] = []
    for i, entry in enumerate(data):
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"manifest[{i}] must be a non-empty path string")
        paths.append(Path(entry))
    return paths


def _load_report(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"report file not found: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"report is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"report must be a JSON object: {path}")
    return data


def compose_session_rollup(
    reports: list[dict[str, Any]],
    *,
    intake: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate finalized per-prompt reports into one shared-schema rollup.

    Output is renderer-consumable (``grain=session_rollup``) with intake strip
    metadata, behavior-mix Craft excerpt, aggregate panes, security max, and
    strongest/weakest exemplars in coaching slots. ``next_actions`` stays empty
    for the host hybrid fill.
    """
    if not reports:
        raise ValueError("compose_session_rollup requires at least one report")
    for i, report in enumerate(reports):
        if not isinstance(report, dict):
            raise ValueError(f"report[{i}] must be a JSON object")

    percents = [float(r.get("percent") or 0.0) for r in reports]
    mean_percent = _round1(_mean(percents))
    band = band_from_percent(mean_percent)
    raw_bands = [str(r.get("band_raw") or r.get("band") or "D") for r in reports]
    # band_raw headline: band from mean of per-prompt percents is already
    # adjusted; expose modal craft-only band when present.
    band_raw = Counter(raw_bands).most_common(1)[0][0]
    if band_raw not in _BAND_ORDER:
        band_raw = band

    intake_meta = _intake_strip(reports, intake)
    if session_id:
        intake_meta["session_id"] = session_id
    rollup_id = (
        session_id
        or intake_meta.get("session_id")
        or f"session-rollup-{len(reports)}"
    )

    out: dict[str, Any] = {
        "id": rollup_id,
        "prompt_id": rollup_id,
        "grain": "session_rollup",
        "percent": mean_percent,
        "band": band,
        "band_raw": band_raw,
        "modifier_reason": _modifier_reason(reports),
        "confidence": _worst_confidence(reports),
        "caps_applied": _union_caps(reports),
        "dimension_scores": _mean_dimensions(reports),
        "rationales": _dimension_rationales(reports),
        "excerpt": _behavior_mix(reports),
        "efficacy": _aggregate_efficacy(reports),
        "planning": _aggregate_planning(reports),
        "security": _aggregate_security(reports),
        "slots": _exemplar_slots(reports),
        "intake": intake_meta,
        "member_prompt_ids": [_prompt_id(r) for r in reports],
    }
    classification = _modal_classification(reports)
    if classification:
        out["classification_summary"] = classification
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compose finalized per-prompt grade JSON into a session rollup"
    )
    report_source = parser.add_mutually_exclusive_group(required=True)
    report_source.add_argument(
        "--reports",
        type=Path,
        nargs="+",
        help="Paths to finalized per-prompt grade-report JSON files",
    )
    report_source.add_argument(
        "--reports-manifest",
        type=Path,
        help="JSON file listing report paths (array of strings; use for 500+ reports on Windows)",
    )
    parser.add_argument(
        "--intake-json",
        type=Path,
        help="Optional intake metadata JSON (tools, window, path, session_id)",
    )
    parser.add_argument(
        "--session-id",
        help="Optional rollup id (defaults to intake.session_id or generated)",
    )
    args = parser.parse_args(argv)

    if args.reports_manifest is not None:
        try:
            report_paths = load_reports_manifest(args.reports_manifest)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        report_paths = list(args.reports)

    reports: list[dict[str, Any]] = []
    for path in report_paths:
        try:
            reports.append(_load_report(path))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    intake: dict[str, Any] | None = None
    if args.intake_json is not None:
        try:
            intake = json.loads(args.intake_json.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            print(f"error: intake file not found: {exc}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as exc:
            print(f"error: intake is not valid JSON: {exc}", file=sys.stderr)
            return 1
        if not isinstance(intake, dict):
            print("error: intake must be a JSON object", file=sys.stderr)
            return 1

    try:
        rollup = compose_session_rollup(
            reports, intake=intake, session_id=args.session_id
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(json.dumps(rollup, indent=2, sort_keys=True))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
