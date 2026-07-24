#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain import EfficacyReport, GradeReport, PlanningReport
from judge_schema import build_grade_report, parse_judge_output
from redact import redact_text
from score_math import apply_outcome_modifier
from store import append_trend_metric, save_grade

_UNAVAILABLE = {"status": "unavailable", "reason": "no session context"}

_EFFICACY_FIELDS: tuple[str, ...] = (
    "session_id",
    "prompts_per_task_mean",
    "single_shot_rate",
    "attributed_rework_rate",
    "worst_task_prompt_count",
    "restates",
    "corrections",
    "abandoned_goal",
)
_PLANNING_FIELDS: tuple[str, ...] = (
    "session_id",
    "planned_decomposition",
    "additive_feature",
    "adaptive_change_with_evidence",
    "scope_change_without_prior_signal",
    "under_specified_initial_plan",
)


def _report_to_dict(report: Any) -> dict[str, Any]:
    return dataclasses.asdict(report)


def confidence_label(mean_kappa: float | None) -> str:
    if mean_kappa is None:
        return "uncalibrated"
    if mean_kappa >= 0.75:
        return "high"
    if mean_kappa >= 0.6:
        return "medium"
    return "low"


def _require_fields(payload: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [f for f in fields if f not in payload]
    if missing:
        raise ValueError(f"{label} missing required field: {missing[0]}")


def _available_efficacy(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, _EFFICACY_FIELDS, "efficacy")
    out = {k: payload[k] for k in _EFFICACY_FIELDS}
    out["status"] = "available"
    return out


def _available_planning(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, _PLANNING_FIELDS, "planning")
    out = {k: payload[k] for k in _PLANNING_FIELDS}
    out["status"] = "available"
    return out


def attach_outcome_axes(
    report: GradeReport,
    *,
    efficacy: dict[str, Any] | None,
    planning: dict[str, Any] | None,
    mean_kappa: float | None,
) -> dict[str, Any]:
    """Flatten craft report and attach Efficacy / Planning (+ optional modifier).

    ``band`` becomes the adjusted headline; ``band_raw`` keeps craft-only band.
    Modifier runs only when both axes are available.
    """
    out = _report_to_dict(report)
    band_raw = report.band
    out["band_raw"] = band_raw

    if efficacy is None:
        out["efficacy"] = dict(_UNAVAILABLE)
    else:
        out["efficacy"] = _available_efficacy(efficacy)

    if planning is None:
        out["planning"] = dict(_UNAVAILABLE)
    else:
        out["planning"] = _available_planning(planning)

    both_available = efficacy is not None and planning is not None
    if both_available:
        eff_obj = EfficacyReport(**{k: efficacy[k] for k in _EFFICACY_FIELDS})
        plan_obj = PlanningReport(**{k: planning[k] for k in _PLANNING_FIELDS})
        adjusted, reason = apply_outcome_modifier(
            band_raw,
            efficacy=eff_obj,
            planning=plan_obj,
            efficacy_high_confidence_user_underspec=bool(
                efficacy.get("high_confidence_user_underspec", False)
            ),
            planning_high_confidence_underspec=bool(
                planning.get("high_confidence_underspec", False)
            ),
            mean_kappa=mean_kappa,
        )
        out["band"] = adjusted
        out["modifier_reason"] = reason
    else:
        out["band"] = band_raw
        out["modifier_reason"] = "no_change"

    return out


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} file not found: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize a grade from judge JSON")
    parser.add_argument("--judge", type=Path, required=True, help="Path to judge output JSON")
    parser.add_argument("--prompt-id", required=True, help="Prompt identifier")
    parser.add_argument("--excerpt", required=True, help="Prompt excerpt (will be redacted)")
    parser.add_argument("--raw", type=Path, default=None, help="Optional raw prompt text path")
    parser.add_argument("--persist-raw", action="store_true", help="Persist raw prompt text")
    parser.add_argument(
        "--model-class",
        choices=["standard", "reasoning", "unknown"],
        default="standard",
        help="Target model class for rubric scoring",
    )
    parser.add_argument(
        "--mean-kappa",
        type=float,
        default=None,
        help="Recorded judge-vs-human mean kappa; drives confidence label and outcome modifier gate",
    )
    parser.add_argument(
        "--efficacy-json",
        type=Path,
        default=None,
        help="Optional EfficacyReport-shaped JSON (+ high_confidence_user_underspec)",
    )
    parser.add_argument(
        "--planning-json",
        type=Path,
        default=None,
        help="Optional PlanningReport-shaped JSON (+ high_confidence_underspec)",
    )
    args = parser.parse_args(argv)

    try:
        judge_data = json.loads(args.judge.read_text(encoding="utf-8"))
        scores, rationales, flags = parse_judge_output(judge_data)
        efficacy_payload = _load_optional_json(args.efficacy_json, "efficacy")
        planning_payload = _load_optional_json(args.planning_json, "planning")
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    report = build_grade_report(
        args.prompt_id,
        scores,
        rationales,
        flags,
        args.model_class,  # type: ignore[arg-type]
    )

    redacted_excerpt, redaction_notes = redact_text(args.excerpt)
    if redaction_notes:
        report.rationales["_redaction_notes"] = ", ".join(redaction_notes)

    try:
        report_dict = attach_outcome_axes(
            report,
            efficacy=efficacy_payload,
            planning=planning_payload,
            mean_kappa=args.mean_kappa,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    report_dict["confidence"] = confidence_label(args.mean_kappa)

    raw_text: str | None = None
    if args.raw is not None:
        try:
            raw_text = args.raw.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            print(f"error: raw file not found: {exc}", file=sys.stderr)
            return 1
        redacted_raw, raw_notes = redact_text(raw_text)
        if raw_notes:
            report_dict["raw_redaction_notes"] = ", ".join(raw_notes)
    else:
        redacted_raw = None

    save_grade(
        report_dict,
        persist_raw=args.persist_raw,
        raw_text=redacted_raw,
        excerpt=redacted_excerpt,
    )

    trend = {
        "prompt_id": report.prompt_id,
        "percent": report.percent,
        "band": report_dict["band"],
        "band_raw": report_dict["band_raw"],
        "modifier_reason": report_dict["modifier_reason"],
        "caps_applied": report.caps_applied,
        "target_model_class": args.model_class,
        "dimension_levels": {s.dimension_id: s.level for s in report.dimension_scores},
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    append_trend_metric(trend)

    print(json.dumps(report_dict, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
