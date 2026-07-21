#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from collections import Counter
from pathlib import Path
from typing import Any

from history_lib import (
    TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS,
    is_coach_completion,
    load_coach_sessions,
    trends_unlock_status,
)


_EFFICIENCY_VALUES = {
    "A+": 4.3,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "D-": 0.7,
    "F": 0.0,
}


def _escape(value: Any, default: str = "") -> str:
    if value is None:
        value = default
    return html.escape(str(value), quote=True)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _completed_label(session: dict[str, Any], index: int) -> str:
    completed_at = session.get("completed_at")
    if isinstance(completed_at, str) and len(completed_at) >= 10:
        return completed_at[:10]
    session_id = session.get("id")
    if session_id:
        return str(session_id)
    return f"Session {index + 1}"


def _dna_value(session: dict[str, Any]) -> tuple[float | None, str]:
    scores = session.get("dna_scores")
    if not isinstance(scores, dict):
        return None, "No DNA score"

    clarity = _float_or_none(scores.get("clarity"))
    if clarity is not None:
        return clarity, f"{clarity:g}"

    numeric_scores = [
        score for score in (_float_or_none(value) for value in scores.values())
        if score is not None
    ]
    if not numeric_scores:
        return None, "No DNA score"

    mean_score = sum(numeric_scores) / len(numeric_scores)
    return mean_score, f"{mean_score:.1f}"


def _efficiency_value(session: dict[str, Any]) -> tuple[float | None, str]:
    scores = session.get("scores")
    if not isinstance(scores, dict):
        return None, "No efficiency grade"

    raw = scores.get("efficiency")
    label = str(raw).strip().upper() if raw is not None else ""
    value = _EFFICIENCY_VALUES.get(label)
    if value is None:
        return None, "No efficiency grade"
    return value, label


def _habit_items(session: dict[str, Any]) -> list[str]:
    raw = session.get("habits_focus")
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if item]


def build_trends_payload(claude_root: Path | None = None) -> dict[str, Any]:
    status = trends_unlock_status(claude_root)
    sessions = load_coach_sessions(claude_root)
    if not status.get("unlocked"):
        return {"status": status, "sessions": []}

    completed_sessions = [
        session for session in sessions
        if isinstance(session, dict) and is_coach_completion(session)
    ]
    completed_sessions.sort(key=lambda session: str(session.get("completed_at") or session.get("id") or ""))
    return {"status": status, "sessions": completed_sessions}


def _base_head(title: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(title)}</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f7f2ff;
  --panel: #ffffff;
  --ink: #182230;
  --muted: #667085;
  --line: #e4e7ec;
  --violet: #7c3aed;
  --cyan: #0891b2;
  --orange: #f97316;
  --green: #16a34a;
  --shadow: 0 24px 64px rgba(24, 34, 48, 0.12);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #10121a;
    --panel: #181b25;
    --ink: #f8fafc;
    --muted: #a4acb9;
    --line: #303647;
    --shadow: 0 24px 64px rgba(0, 0, 0, 0.35);
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background:
    radial-gradient(circle at 8% 8%, rgba(124, 58, 237, 0.24), transparent 26rem),
    radial-gradient(circle at 92% 12%, rgba(8, 145, 178, 0.20), transparent 24rem),
    var(--bg);
  color: var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}}
.page {{
  max-width: 1120px;
  margin: 0 auto;
  padding: 48px 20px;
}}
.hero, .panel {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 28px;
  box-shadow: var(--shadow);
}}
.hero {{ padding: 36px; margin-bottom: 24px; }}
.eyebrow {{
  color: var(--violet);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin: 0 0 10px;
  text-transform: uppercase;
}}
h1, h2, h3, p {{ margin-top: 0; }}
h1 {{ font-size: clamp(2.35rem, 7vw, 4.8rem); line-height: 0.95; margin-bottom: 12px; }}
h2 {{ font-size: 1.35rem; margin-bottom: 14px; }}
h3 {{ font-size: 1rem; margin-bottom: 8px; }}
.subtitle, .muted, li {{ color: var(--muted); }}
.panel {{ margin-top: 24px; padding: 28px; }}
.chart-grid {{
  display: grid;
  gap: 24px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}}
.chart-grid .wide {{ grid-column: 1 / -1; }}
.chart-frame {{
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 18px;
}}
.chart-frame svg {{
  display: block;
  height: auto;
  width: 100%;
}}
.axis {{ stroke: var(--line); stroke-width: 2; }}
.grid {{ stroke: var(--line); stroke-width: 1; opacity: 0.72; }}
.label {{ fill: var(--muted); font-size: 12px; }}
.value-label {{ fill: var(--ink); font-size: 13px; font-weight: 700; }}
.empty {{ color: var(--muted); margin-bottom: 0; }}
.locked-count {{
  color: var(--violet);
  display: block;
  font-size: clamp(3rem, 12vw, 7rem);
  font-weight: 900;
  letter-spacing: -0.08em;
  line-height: 1;
  margin: 22px 0;
}}
ol {{ margin-bottom: 0; padding-left: 1.3rem; }}
li + li {{ margin-top: 8px; }}
@media (max-width: 760px) {{
  .chart-grid {{ grid-template-columns: 1fr; }}
  .hero, .panel {{ padding: 26px; }}
}}
</style>
</head>
<body>
<main class="page">
"""


def _end_document() -> str:
    return """</main>
</body>
</html>
"""


def _render_locked_html(status: dict[str, Any]) -> str:
    completed = int(status.get("completed") or 0)
    required = int(status.get("required") or TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS)
    remaining = max(0, required - completed)
    session_word = "session" if remaining == 1 else "sessions"
    return (
        _base_head("Prompt Trends Locked")
        + f"""  <section class="hero">
    <p class="eyebrow">Prompt trends</p>
    <h1>Keep coaching to reveal your multi-week view.</h1>
    <p class="subtitle">Trend charts appear after enough completed coach sessions to make the patterns useful.</p>
    <strong class="locked-count">{completed}/{required}</strong>
    <p class="muted">Complete {remaining} more coach {session_word} to reach the {required}-session requirement.</p>
  </section>

  <section class="panel">
    <h2>What counts as a coach completion?</h2>
    <ol>
      <li>The coach session is marked completed.</li>
      <li>The live assessment is finished.</li>
      <li>At least one coaching drill round is recorded.</li>
    </ol>
  </section>
"""
        + _end_document()
    )


def _line_chart(
    title: str,
    description: str,
    points: list[tuple[str, float, str]],
    *,
    color: str,
    fill: str,
    max_value: float,
    unit: str,
) -> str:
    if not points:
        return (
            '<article class="chart-frame">'
            f"<h3>{_escape(title)}</h3>"
            f'<p class="empty">{_escape(description)}</p>'
            "</article>"
        )

    width = 640
    height = 260
    left = 48
    right = 24
    top = 24
    bottom = 54
    chart_width = width - left - right
    chart_height = height - top - bottom
    denom = max(1, len(points) - 1)

    coords = []
    labels = []
    for index, (label, value, display) in enumerate(points):
        bounded = max(0.0, min(max_value, value))
        x = left + (chart_width * index / denom)
        y = top + chart_height - (chart_height * bounded / max_value)
        coords.append((x, y, label, display))
        labels.append(
            f'<text class="label" x="{x:.1f}" y="{height - 18}" text-anchor="middle">{_escape(label)}</text>'
        )

    polygon_points = (
        f"{left},{top + chart_height} "
        + " ".join(f"{x:.1f},{y:.1f}" for x, y, _label, _display in coords)
        + f" {left + chart_width},{top + chart_height}"
    )
    polyline_points = " ".join(f"{x:.1f},{y:.1f}" for x, y, _label, _display in coords)
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#ffffff" stroke-width="2">'
        f"<title>{_escape(label)}: {_escape(display)}{_escape(unit)}</title>"
        "</circle>"
        for x, y, label, display in coords
    )
    value_labels = "\n".join(
        f'<text class="value-label" x="{x:.1f}" y="{max(14, y - 12):.1f}" text-anchor="middle">{_escape(display)}</text>'
        for x, y, _label, display in coords
    )

    return f"""<article class="chart-frame">
  <h3>{_escape(title)}</h3>
  <p class="muted">{_escape(description)}</p>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)} chart">
    <line class="axis" x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" y2="{top + chart_height}"></line>
    <line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}"></line>
    <line class="grid" x1="{left}" y1="{top}" x2="{left + chart_width}" y2="{top}"></line>
    <line class="grid" x1="{left}" y1="{top + chart_height / 2:.1f}" x2="{left + chart_width}" y2="{top + chart_height / 2:.1f}"></line>
    <text class="label" x="{left - 10}" y="{top + 4}" text-anchor="end">{max_value:g}</text>
    <text class="label" x="{left - 10}" y="{top + chart_height + 4}" text-anchor="end">0</text>
    <polygon points="{polygon_points}" fill="{fill}"></polygon>
    <polyline points="{polyline_points}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
    {circles}
    {value_labels}
    {"".join(labels)}
  </svg>
</article>"""


def _bar_chart(title: str, description: str, counts: Counter[str]) -> str:
    if not counts:
        return (
            '<article class="chart-frame wide">'
            f"<h3>{_escape(title)}</h3>"
            f'<p class="empty">{_escape(description)}</p>'
            "</article>"
        )

    items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    width = 760
    bar_height = 30
    gap = 18
    left = 160
    right = 34
    top = 30
    bottom = 30
    height = top + bottom + len(items) * bar_height + (len(items) - 1) * gap
    chart_width = width - left - right
    max_count = max(count for _habit, count in items)
    colors = ["#7c3aed", "#0891b2", "#f97316", "#16a34a", "#db2777", "#ca8a04", "#2563eb", "#dc2626"]

    bars = []
    for index, (habit, count) in enumerate(items):
        y = top + index * (bar_height + gap)
        bar_width = chart_width * count / max_count
        color = colors[index % len(colors)]
        bars.append(
            f'<text class="label" x="{left - 12}" y="{y + 20}" text-anchor="end">{_escape(habit)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" rx="10" fill="{color}"></rect>'
            f'<text class="value-label" x="{left + bar_width + 10:.1f}" y="{y + 20}">{count}</text>'
        )

    return f"""<article class="chart-frame wide">
  <h3>{_escape(title)}</h3>
  <p class="muted">{_escape(description)}</p>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)} chart">
    <line class="axis" x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}"></line>
    {"".join(bars)}
  </svg>
</article>"""


def _render_unlocked_html(payload: dict[str, Any]) -> str:
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        sessions = []

    dna_points: list[tuple[str, float, str]] = []
    efficiency_points: list[tuple[str, float, str]] = []
    habits: Counter[str] = Counter()

    for index, session in enumerate(sessions):
        if not isinstance(session, dict):
            continue
        label = _completed_label(session, index)
        dna_value, dna_display = _dna_value(session)
        if dna_value is not None:
            dna_points.append((label, dna_value, dna_display))
        efficiency_value, efficiency_display = _efficiency_value(session)
        if efficiency_value is not None:
            efficiency_points.append((label, efficiency_value, efficiency_display))
        habits.update(_habit_items(session))

    status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    completed = int(status.get("completed") or len(sessions))
    return (
        _base_head("Prompt Trends")
        + f"""  <section class="hero">
    <p class="eyebrow">Prompt trends</p>
    <h1>Your colorful multi-week Prompt Trend view.</h1>
    <p class="subtitle">Built from {completed} completed coach sessions, with inline SVG charts for DNA clarity, efficiency, and habit focus.</p>
  </section>

  <section class="panel">
    <h2>Charts</h2>
    <div class="chart-grid">
      {_line_chart(
          "DNA clarity",
          "Clarity score by completed coach session; mean DNA is used when clarity is not present.",
          dna_points,
          color="#7c3aed",
          fill="rgba(124, 58, 237, 0.16)",
          max_value=10,
          unit="/10",
      )}
      {_line_chart(
          "Efficiency grade",
          "Letter grades mapped to a 0-4.3 scale so progress can be charted.",
          efficiency_points,
          color="#0891b2",
          fill="rgba(8, 145, 178, 0.16)",
          max_value=4.3,
          unit="",
      )}
      {_bar_chart(
          "Habit focus frequency",
          "Most frequent coaching habit focus areas across completed sessions.",
          habits,
      )}
    </div>
  </section>
"""
        + _end_document()
    )


def render_trends_html(payload: dict[str, Any]) -> str:
    status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    if not status.get("unlocked"):
        return _render_locked_html(status)
    return _render_unlocked_html(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render gated prompting trends HTML")
    parser.add_argument("--root", type=Path, default=None, help="Claude root containing grader history")
    parser.add_argument("--out", type=Path, required=True, help="Trends HTML output path")
    args = parser.parse_args(argv)

    payload = build_trends_payload(args.root)
    html_text = render_trends_html(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
