"""Deterministic HTML grade-report renderer (Tri-pane cockpit)."""
from __future__ import annotations

import argparse
import html
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

_CSS = """\
:root{--ink:#e8ecf4;--muted:#8b95ab;--line:#2a3142;--pane:#151924;--bg:#10131a;--top:#161a24;--band:#f0a35e;--danger:#9b1c1c;--ok:#1f6f5b;--slot:#1a2030}
*{box-sizing:border-box}
body{margin:0;font-family:"IBM Plex Sans","Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}
.grade-report{min-height:100vh;display:grid;grid-template-rows:auto auto 1fr auto}
.topbar{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;padding:1rem 1.25rem;border-bottom:1px solid var(--line);background:var(--top)}
.band-letter{font-weight:700;font-size:2.2rem;color:var(--band);vertical-align:-0.2rem}
.meta-muted{color:var(--muted)}
.panes{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);min-height:14rem}
.pane{background:var(--pane);padding:1rem 1.1rem}
.pane h2{margin:0 0 0.75rem;font-size:0.75rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted)}
.metric{font-size:1.4rem;font-variant-numeric:tabular-nums;margin:0.2rem 0}
.dims{padding:0.75rem 1.25rem 1rem;background:#0e1118}
.dim-chips{display:flex;flex-wrap:wrap;gap:0.4rem}
.chip{border:1px solid #333b4f;border-radius:999px;padding:0.25rem 0.55rem;font-size:0.78rem;color:#b7c0d4}
.chip.na{opacity:0.45}
details.rationale{margin-top:0.5rem;color:var(--muted);font-size:0.85rem}
.coaching{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line)}
.slot-box{background:var(--slot);padding:0.75rem 0.9rem;min-height:5.5rem;color:#c5cee0}
.slot-box h3{margin:0 0 0.4rem;font-size:0.75rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted)}
.slot-box .hint{color:var(--muted);font-size:0.85rem}
.security-ok{border-left:4px solid var(--ok);background:#e7f3ee;color:#12141a;padding:0.75rem 1rem}
.security-hit{border-left:4px solid var(--danger);background:#f8e8e8;color:#12141a;padding:0.75rem 1rem}
ul.callouts,ol.actions{margin:0.4rem 0 0;padding-left:1.2rem}
@media(max-width:900px){.panes,.coaching{grid-template-columns:1fr}}
"""


def _esc(value: Any, default: str = "") -> str:
    if value is None:
        value = default
    return html.escape(str(value), quote=True)


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


def _security_aside(security: dict[str, Any] | None) -> str:
    if not security or security.get("status") in (None, "none", "clear"):
        return '<aside class="security-ok" data-region="security">none detected</aside>'
    parts: list[str] = []
    severity = security.get("severity")
    if severity:
        parts.append(f"severity: {_esc(severity)}")
    summary = security.get("summary")
    if summary:
        parts.append(_esc(summary))
    action = security.get("action")
    if action:
        parts.append(f"action: {_esc(action)}")
    body = "<br/>".join(parts) if parts else "none detected"
    cls = "security-ok" if body == "none detected" else "security-hit"
    return f'<aside class="{cls}" data-region="security">{body}</aside>'


def _coaching_section(slots: dict[str, Any] | None) -> str:
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

    if strongest:
        strong_html = f"<p>{_esc(_truncate(str(strongest), STRONG_CAP))}</p>"
    else:
        strong_html = f'<p class="hint">{_esc(_EMPTY_STRONG)}</p>'

    if weakest:
        weak_html = f"<p>{_esc(_truncate(str(weakest), WEAK_CAP))}</p>"
    else:
        weak_html = f'<p class="hint">{_esc(_EMPTY_WEAK)}</p>'

    actions: list[str]
    if isinstance(next_actions, list) and next_actions:
        actions = [_truncate(str(a), ACTION_CAP) for a in next_actions[:ACTION_COUNT]]
        while len(actions) < ACTION_COUNT:
            actions.append("")
        action_items = []
        for a in actions:
            if a:
                action_items.append(f"<li>{_esc(a)}</li>")
            else:
                action_items.append(f'<li class="hint">{_esc(_EMPTY_ACTION)}</li>')
    elif isinstance(next_actions, str) and next_actions.strip():
        action_items = [
            f"<li>{_esc(_truncate(next_actions.strip(), ACTION_CAP))}</li>",
            f'<li class="hint">{_esc(_EMPTY_ACTION)}</li>',
            f'<li class="hint">{_esc(_EMPTY_ACTION)}</li>',
        ]
    else:
        action_items = [
            f'<li class="hint">{_esc(_EMPTY_ACTION)}</li>' for _ in range(ACTION_COUNT)
        ]

    return "\n".join(
        [
            '<section class="coaching" data-region="coaching">',
            f'<div class="slot-box"><h3>Strongest</h3>{strong_html}</div>',
            f'<div class="slot-box"><h3>Weakest</h3>{weak_html}</div>',
            (
                '<div class="slot-box"><h3>Next actions</h3>'
                f'<ol class="actions">{"".join(action_items)}</ol></div>'
            ),
            "</section>",
        ]
    )


def _efficacy_pane(
    efficacy: dict[str, Any], classification: dict[str, Any] | None
) -> str:
    if efficacy.get("status") != "available":
        reason = efficacy.get("reason") or "unavailable"
        return "\n".join(
            [
                '<section class="pane" data-region="efficacy">',
                "<h2>Efficacy</h2>",
                f"<p>unavailable — {_esc(reason)}</p>",
                "</section>",
            ]
        )
    rate = float(efficacy.get("attributed_rework_rate") or 0.0)
    rate_pct = f"{rate * 100:.0f}%"
    abandoned = bool(efficacy.get("abandoned_goal"))
    lines = [
        '<section class="pane" data-region="efficacy">',
        "<h2>Efficacy</h2>",
        f'<p class="metric">attributed rework: {_esc(rate_pct)}</p>',
        (
            f'<p class="meta-muted">restates {_esc(efficacy.get("restates", 0))} · '
            f'corrections {_esc(efficacy.get("corrections", 0))} · '
            f'prompts/task {_esc(efficacy.get("prompts_per_task_mean", 0))} · '
            f'single_shot {_esc(efficacy.get("single_shot_rate", 0))} · '
            f'worst {_esc(efficacy.get("worst_task_prompt_count", 0))} · '
            f"abandoned_goal {_fmt_bool(abandoned)}</p>"
        ),
    ]
    attr = _attribution(efficacy, classification)
    if attr:
        lines.append(f"<p>attribution: {_esc(attr)}</p>")
    lines.append("</section>")
    return "\n".join(lines)


def _planning_pane(planning: dict[str, Any]) -> str:
    if planning.get("status") != "available":
        reason = planning.get("reason") or "unavailable"
        return "\n".join(
            [
                '<section class="pane" data-region="planning">',
                "<h2>Planning</h2>",
                f"<p>unavailable — {_esc(reason)}</p>",
                "</section>",
            ]
        )
    lines = [
        '<section class="pane" data-region="planning">',
        "<h2>Planning</h2>",
        "<ul>",
        f"<li>planned_decomposition: {_esc(planning.get('planned_decomposition', 0))}</li>",
        f"<li>under_specified_initial_plan: {_esc(planning.get('under_specified_initial_plan', 0))}</li>",
        f"<li>scope_change_without_prior_signal: {_esc(planning.get('scope_change_without_prior_signal', 0))}</li>",
        f"<li>additive_feature: {_esc(planning.get('additive_feature', 0))}</li>",
        f"<li>adaptive_change_with_evidence: {_esc(planning.get('adaptive_change_with_evidence', 0))}</li>",
        "</ul>",
    ]
    callouts = _planning_callouts(planning)
    if callouts:
        lines.append('<p class="meta-muted">callouts:</p>')
        lines.append('<ul class="callouts">')
        for c in callouts:
            lines.append(f"<li>{_esc(c)}</li>")
        lines.append("</ul>")
    lines.append("</section>")
    return "\n".join(lines)


def _dimensions_section(
    scores: list[dict[str, Any]], rationales: dict[str, str]
) -> str:
    chips: list[str] = []
    details: list[str] = []
    for s in scores:
        dim = str(s["dimension_id"])
        level = s["level"]
        na = str(level).upper() == "N/A"
        cls = ' class="chip na"' if na else ' class="chip"'
        chips.append(f"<span{cls}>{_esc(dim)} {_esc(level)}</span>")
        text = rationales.get(dim, "")
        details.append(
            f'<details class="rationale"><summary>{_esc(dim)}</summary>{_esc(text)}</details>'
        )
    return "\n".join(
        [
            '<section class="dims" data-region="dimensions">',
            '<div class="meta-muted">Dimensions</div>',
            '<div class="dim-chips">',
            *chips,
            "</div>",
            *details,
            "</section>",
        ]
    )


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


def render_grade_html(report: dict[str, Any]) -> str:
    """Render a finalized grade-report dict as contracted Tri-pane HTML."""
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
    dim_rationales = {
        k: v for k, v in rationales.items() if k.startswith("D") and k[1:].isdigit()
    }
    classification = report.get("classification_summary")
    security = report.get("security")
    slots = report.get("slots")
    title_prefix = "Session rollup" if is_rollup else "Grade report"
    craft_label = "behavior mix" if is_rollup else "excerpt"
    intake_line = _intake_line(
        report.get("intake") if isinstance(report.get("intake"), dict) else None
    )

    craft_pane = "\n".join(
        [
            '<section class="pane" data-region="craft">',
            "<h2>Craft</h2>",
            f'<p class="metric">{_esc(band)}</p>',
            f'<p class="meta-muted">{_esc(craft_label)}: {_esc(excerpt)}</p>',
            f'<p class="meta-muted">caps: {_esc(_caps_line(caps))}</p>',
            "</section>",
        ]
    )

    topbar_left = [
        "<div>",
        f'<div class="meta-muted">{_esc(prompt_id)}</div>',
    ]
    if is_rollup and intake_line:
        topbar_left.append(f'<div class="meta-muted">{_esc(intake_line)}</div>')
    topbar_left.extend(
        [
            (
                f'<div>Craft <span class="band-letter">{_esc(band)}</span> '
                f'<span class="meta-muted">raw {_esc(band_raw)} · '
                f"~{_esc(_fmt_percent(float(percent)))}% · "
                f"confidence {_esc(confidence)}</span></div>"
            ),
            f'<div class="meta-muted">modifier: {_esc(modifier)}</div>',
            "</div>",
        ]
    )

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8"/>',
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>',
        f"<title>{_esc(title_prefix)} · {_esc(prompt_id)}</title>",
        "<style>",
        _CSS.rstrip("\n"),
        "</style>",
        "</head>",
        "<body>",
        (
            f'<article class="grade-report" data-prompt-id="{_esc(prompt_id)}"'
            + (f' data-grain="{_esc(grain)}"' if grain else "")
            + ">"
        ),
        '<header class="topbar" data-region="topbar">',
        *topbar_left,
        _security_aside(security if isinstance(security, dict) else None),
        "</header>",
        '<div class="panes">',
        craft_pane,
        _efficacy_pane(
            efficacy, classification if isinstance(classification, dict) else None
        ),
        _planning_pane(planning),
        "</div>",
        _dimensions_section(scores, dim_rationales),
        _coaching_section(slots if isinstance(slots, dict) else None),
        "</article>",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render finalized grade JSON as contracted Tri-pane HTML"
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
    sys.stdout.write(render_grade_html(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
