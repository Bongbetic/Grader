"""Deterministic markdown grade-report renderer (Tri-pane cockpit twin)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STRONG_CAP = 120
WEAK_CAP = 120
ACTION_CAP = 80
ACTION_COUNT = 3

_PLANNING_CALLOUT_KEYS: tuple[str, ...] = (
    "planned_decomposition",
    "under_specified_initial_plan",
    "scope_change_without_prior_signal",
    "additive_feature",
    "adaptive_change_with_evidence",
)

_EMPTY_STRONG = "_(empty — fill <=120 chars)_"
_EMPTY_WEAK = "_(empty — fill <=120 chars)_"
_EMPTY_ACTION = "_(empty — fill <=80 chars)_"


def _truncate(text: str, cap: int) -> str:
    if len(text) <= cap:
        return text
    return text[:cap]


def _fmt_bool(value: bool) -> str:
    return "true" if value else "false"


def _fmt_percent(value: float) -> str:
    rounded = round(float(value), 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.1f}"


def _caps_line(caps: list[Any] | None) -> str:
    if not caps:
        return "none"
    return ", ".join(str(c) for c in caps)


def _attribution(efficacy: dict[str, Any], classification: dict[str, Any] | None) -> str | None:
    if not classification:
        return None
    cause = classification.get("rework_cause")
    restates = int(efficacy.get("restates") or 0)
    if cause == "user_under_specified" and restates:
        return f"{restates} restates attributed to under-specified opener — not agent misread."
    if cause == "agent_misread" and restates:
        return f"{restates} restates — agent misread, not your prompt."
    return None


def _planning_callouts(planning: dict[str, Any]) -> list[str]:
    if "callouts" in planning and isinstance(planning["callouts"], list):
        out: list[str] = []
        for item in planning["callouts"]:
            if isinstance(item, dict) and "text" in item:
                out.append(str(item["text"]))
            else:
                out.append(str(item))
        return out
    out = []
    for key in _PLANNING_CALLOUT_KEYS:
        count = int(planning.get(key) or 0)
        if count:
            out.append(f"{key} ×{count}")
    return out


def _security_block(security: dict[str, Any] | None) -> str:
    if not security or security.get("status") in (None, "none", "clear"):
        return "none detected"
    lines: list[str] = []
    severity = security.get("severity")
    if severity:
        lines.append(f"severity: {severity}")
    summary = security.get("summary")
    if summary:
        lines.append(str(summary))
    action = security.get("action")
    if action:
        lines.append(f"action: {action}")
    return "\n".join(lines) if lines else "none detected"


def _coaching_block(slots: dict[str, Any] | None) -> str:
    slots = slots or {}
    strongest = slots.get("strongest")
    weakest = slots.get("weakest")
    next_actions = slots.get("next_actions")

    if isinstance(strongest, dict):
        strongest = strongest.get("text")
    if isinstance(weakest, dict):
        weakest = weakest.get("text")
    if isinstance(next_actions, dict):
        next_actions = next_actions.get("items") or next_actions.get("text")

    strong_line = (
        _truncate(str(strongest), STRONG_CAP) if strongest else _EMPTY_STRONG
    )
    weak_line = _truncate(str(weakest), WEAK_CAP) if weakest else _EMPTY_WEAK

    actions: list[str]
    if isinstance(next_actions, list) and next_actions:
        actions = [_truncate(str(a), ACTION_CAP) for a in next_actions[:ACTION_COUNT]]
        while len(actions) < ACTION_COUNT:
            actions.append(_EMPTY_ACTION)
    elif isinstance(next_actions, str) and next_actions.strip():
        actions = [_truncate(next_actions.strip(), ACTION_CAP)] + [_EMPTY_ACTION] * (
            ACTION_COUNT - 1
        )
    else:
        actions = [_EMPTY_ACTION] * ACTION_COUNT

    lines = [
        "### Strongest",
        strong_line,
        "",
        "### Weakest",
        weak_line,
        "",
        "### Next actions",
    ]
    for i, action in enumerate(actions, start=1):
        lines.append(f"{i}. {action}")
    return "\n".join(lines)


def _efficacy_block(
    efficacy: dict[str, Any], classification: dict[str, Any] | None
) -> str:
    if efficacy.get("status") != "available":
        reason = efficacy.get("reason") or "unavailable"
        return f"unavailable — {reason}"
    rate = float(efficacy.get("attributed_rework_rate") or 0.0)
    rate_pct = f"{rate * 100:.0f}%"
    abandoned = bool(efficacy.get("abandoned_goal"))
    lines = [
        f"attributed rework: {rate_pct}",
        (
            f"restates {efficacy.get('restates', 0)} · "
            f"corrections {efficacy.get('corrections', 0)} · "
            f"prompts/task {efficacy.get('prompts_per_task_mean', 0)} · "
            f"single_shot {efficacy.get('single_shot_rate', 0)} · "
            f"worst {efficacy.get('worst_task_prompt_count', 0)} · "
            f"abandoned_goal {_fmt_bool(abandoned)}"
        ),
    ]
    attr = _attribution(efficacy, classification)
    if attr:
        lines.append(f"attribution: {attr}")
    return "\n".join(lines)


def _planning_block(planning: dict[str, Any]) -> str:
    if planning.get("status") != "available":
        reason = planning.get("reason") or "unavailable"
        return f"unavailable — {reason}"
    lines = [
        f"- planned_decomposition: {planning.get('planned_decomposition', 0)}",
        f"- under_specified_initial_plan: {planning.get('under_specified_initial_plan', 0)}",
        f"- scope_change_without_prior_signal: {planning.get('scope_change_without_prior_signal', 0)}",
        f"- additive_feature: {planning.get('additive_feature', 0)}",
        f"- adaptive_change_with_evidence: {planning.get('adaptive_change_with_evidence', 0)}",
    ]
    callouts = _planning_callouts(planning)
    if callouts:
        lines.append("callouts:")
        for c in callouts:
            lines.append(f"- {c}")
    return "\n".join(lines)


def _dimensions_block(
    scores: list[dict[str, Any]], rationales: dict[str, str]
) -> str:
    chips = " · ".join(
        f"{s['dimension_id']} {s['level']}" for s in scores
    )
    lines = [chips, "", "### Rationales"]
    for s in scores:
        dim = s["dimension_id"]
        text = rationales.get(dim, "")
        lines.append(f"**{dim}:** {text}")
    return "\n".join(lines)


def _intake_line(intake: dict[str, Any] | None) -> str | None:
    if not intake:
        return None
    count = intake.get("prompt_count")
    tools = intake.get("tools") or []
    tool_bit = ",".join(str(t) for t in tools) if tools else "unknown"
    path = intake.get("intake_path") or "unknown"
    line = f"intake: {count} prompts · tools={tool_bit} · path={path}"
    start = intake.get("window_start")
    end = intake.get("window_end")
    if start or end:
        line += f" · window={start or '?'}…{end or '?'}"
    return line


def render_grade_markdown(report: dict[str, Any]) -> str:
    """Render a finalized grade-report dict as contracted markdown."""
    prompt_id = report.get("prompt_id") or report.get("id") or "unknown"
    grain = report.get("grain")
    is_rollup = grain == "session_rollup"
    band = report.get("band", "?")
    band_raw = report.get("band_raw", band)
    percent = report.get("percent", 0)
    confidence = report.get("confidence", "uncalibrated")
    modifier = report.get("modifier_reason", "no_change")
    excerpt = report.get("excerpt") or "_(none)_"
    caps = report.get("caps_applied") or []
    efficacy = report.get("efficacy") or {
        "status": "unavailable",
        "reason": "no session context",
    }
    planning = report.get("planning") or {
        "status": "unavailable",
        "reason": "no session context",
    }
    scores = report.get("dimension_scores") or []
    rationales = report.get("rationales") or {}
    # Drop internal redaction notes from dimension rationale section
    dim_rationales = {
        k: v for k, v in rationales.items() if k.startswith("D") and k[1:].isdigit()
    }
    classification = report.get("classification_summary")
    security = report.get("security")
    slots = report.get("slots")
    title = f"# Session rollup · {prompt_id}" if is_rollup else f"# Grade report · {prompt_id}"
    craft_label = "behavior mix" if is_rollup else "excerpt"
    topbar = [
        "## Topbar",
    ]
    intake_line = _intake_line(
        report.get("intake") if isinstance(report.get("intake"), dict) else None
    )
    if is_rollup and intake_line:
        topbar.append(intake_line)
    topbar.extend(
        [
            f"Craft **{band}** (raw {band_raw}) · ~{_fmt_percent(float(percent))}% · confidence {confidence}",
            f"modifier: {modifier}",
        ]
    )

    parts = [
        title,
        "",
        *topbar,
        "",
        "## Craft",
        f"{craft_label}: {excerpt}",
        f"caps: {_caps_line(caps)}",
        "",
        "## Efficacy",
        _efficacy_block(efficacy, classification if isinstance(classification, dict) else None),
        "",
        "## Planning",
        _planning_block(planning),
        "",
        "## Dimensions",
        _dimensions_block(scores, dim_rationales),
        "",
        "## Security",
        _security_block(security if isinstance(security, dict) else None),
        "",
        "## Coaching",
        "",
        _coaching_block(slots if isinstance(slots, dict) else None),
        "",
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render finalized grade JSON as contracted markdown"
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to finalized grade-report JSON",
    )
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.report.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        print(f"error: report file not found: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: report is not valid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("error: report must be a JSON object", file=sys.stderr)
        return 1
    sys.stdout.write(render_grade_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
