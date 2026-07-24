#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def _escape(value: Any, default: str = "") -> str:
    if value is None:
        value = default
    return html.escape(str(value), quote=True)


def _score_value(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(10.0, score))


def _score_label(value: Any) -> str:
    score = _score_value(value)
    return f"{score:g}/10"


def _letter(value: Any) -> str:
    return _escape(value, default="--")


def _render_score_cards(scores: dict[str, Any]) -> str:
    cards = []
    for key, label in (
        ("skill", "Skill"),
        ("efficiency", "Efficiency"),
        ("consistency", "Consistency"),
    ):
        cards.append(
            '<article class="score-card">'
            f'<span class="score-label">{label}</span>'
            f'<strong class="score-letter">{_letter(scores.get(key))}</strong>'
            "</article>"
        )
    return "\n".join(cards)


def _render_dna_bar(score: Any, label: str) -> str:
    value = _score_value(score)
    width = value * 10.0
    return (
        f'<svg class="dna-bar" viewBox="0 0 100 10" role="img" aria-label="{label} {_score_label(score)}">'
        '<rect class="dna-track" x="0" y="0" width="100" height="10" rx="5"></rect>'
        f'<rect class="dna-fill" x="0" y="0" width="{width:.1f}" height="10" rx="5"></rect>'
        "</svg>"
    )


def _render_dna(dna: list[Any]) -> str:
    if not dna:
        return '<p class="empty">No DNA dimensions were scored.</p>'

    items = []
    for raw in dna:
        dim = raw if isinstance(raw, dict) else {}
        label = _escape(dim.get("label") or dim.get("id") or "Dimension")
        score = dim.get("score")
        verdict = _escape(dim.get("verdict"), default="No verdict recorded.")
        evidence = dim.get("evidence") or []
        if not isinstance(evidence, list):
            evidence = [evidence]
        evidence_items = "\n".join(
            f"<li>{_escape(item)}</li>" for item in evidence if item is not None
        )
        evidence_html = (
            f'<ul class="evidence">{evidence_items}</ul>' if evidence_items else ""
        )
        items.append(
            '<article class="dna-item">'
            '<div class="dna-heading">'
            f"<h3>{label}</h3>"
            f'<span class="dna-score">{_score_label(score)}</span>'
            "</div>"
            f'{_render_dna_bar(score, label)}'
            f'<p class="verdict">{verdict}</p>'
            f"{evidence_html}"
            "</article>"
        )
    return "\n".join(items)


def _render_habits(habits: list[Any]) -> str:
    if not habits:
        return ""
    items = []
    for habit in habits:
        if isinstance(habit, dict):
            text = habit.get("text") or habit.get("title") or habit.get("habit")
        else:
            text = habit
        if text is not None:
            items.append(f"<li>{_escape(text)}</li>")
    if not items:
        return ""
    return (
        '<section class="panel">'
        "<h2>Habits</h2>"
        f'<ul class="habits">{"".join(items)}</ul>'
        "</section>"
    )


def _render_learning_cards(cards: list[Any]) -> str:
    if not cards:
        return ""
    rendered = []
    for card in cards:
        if isinstance(card, dict):
            title = _escape(card.get("title") or card.get("name") or "Learning card")
            body = _escape(card.get("body") or card.get("description") or "")
        else:
            title = "Learning card"
            body = _escape(card)
        body_html = f'<p>{body}</p>' if body else ""
        rendered.append(
            '<article class="learning-card">'
            f"<h3>{title}</h3>"
            f"{body_html}"
            "</article>"
        )
    return (
        '<section class="panel">'
        "<h2>Learning Cards</h2>"
        f'<div class="learning-grid">{"".join(rendered)}</div>'
        "</section>"
    )


def render_profile_html(profile: dict[str, Any]) -> str:
    scores = profile.get("scores") if isinstance(profile.get("scores"), dict) else {}
    dna = profile.get("dna") if isinstance(profile.get("dna"), list) else []
    habits = profile.get("habits") if isinstance(profile.get("habits"), list) else []
    learning_cards = (
        profile.get("learning_cards")
        if isinstance(profile.get("learning_cards"), list)
        else []
    )
    overall_letter = _letter(profile.get("overall_letter"))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Prompting Profile</title>
<style>
:root {{
  color-scheme: light dark;
  --bg: #f6f4ef;
  --panel: #ffffff;
  --ink: #1f2933;
  --muted: #667085;
  --line: #e4e7ec;
  --accent: #6957d5;
  --accent-soft: #ece9ff;
  --bar-track: #e5e7eb;
  --shadow: 0 20px 50px rgba(31, 41, 51, 0.10);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #101218;
    --panel: #171a22;
    --ink: #f2f4f7;
    --muted: #a4acb9;
    --line: #2b303b;
    --accent: #a99cff;
    --accent-soft: #28233f;
    --bar-track: #303646;
    --shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: radial-gradient(circle at top left, var(--accent-soft), transparent 34rem), var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}}
.report {{
  max-width: 1040px;
  margin: 0 auto;
  padding: 48px 20px;
}}
.hero, .panel {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 28px;
  box-shadow: var(--shadow);
}}
.hero {{
  display: grid;
  gap: 24px;
  grid-template-columns: 1fr auto;
  align-items: center;
  padding: 36px;
  margin-bottom: 24px;
}}
.eyebrow {{
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin: 0 0 10px;
  text-transform: uppercase;
}}
h1, h2, h3, p {{ margin-top: 0; }}
h1 {{ font-size: clamp(2.35rem, 7vw, 5rem); line-height: 0.95; margin-bottom: 12px; }}
h2 {{ font-size: 1.35rem; margin-bottom: 18px; }}
h3 {{ font-size: 1rem; margin-bottom: 6px; }}
.subtitle {{ color: var(--muted); margin-bottom: 0; max-width: 46rem; }}
.overall {{
  border: 1px solid var(--line);
  border-radius: 22px;
  min-width: 132px;
  padding: 18px;
  text-align: center;
}}
.overall-label, .score-label, .dna-score {{
  color: var(--muted);
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}
.overall-letter {{ color: var(--accent); display: block; font-size: 3.4rem; line-height: 1; }}
.scores {{
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 24px;
}}
.score-card {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 22px;
}}
.score-letter {{ color: var(--accent); display: block; font-size: 2.2rem; }}
.panel {{ margin-top: 24px; padding: 28px; }}
.dna-grid, .learning-grid {{
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}}
.dna-item, .learning-card {{
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 18px;
}}
.dna-heading {{
  align-items: baseline;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}}
.dna-bar {{ display: block; height: 10px; margin: 10px 0 12px; width: 100%; }}
.dna-track {{ fill: var(--bar-track); }}
.dna-fill {{ fill: var(--accent); }}
.verdict, .learning-card p {{ color: var(--muted); margin-bottom: 0; }}
.evidence, .habits {{ margin-bottom: 0; padding-left: 1.2rem; }}
.evidence {{ color: var(--muted); font-size: 0.92rem; margin-top: 12px; }}
.habits li + li, .evidence li + li {{ margin-top: 8px; }}
.empty {{ color: var(--muted); margin-bottom: 0; }}
@media (max-width: 720px) {{
  .hero, .scores, .dna-grid, .learning-grid {{ grid-template-columns: 1fr; }}
  .hero {{ padding: 28px; }}
}}
</style>
</head>
<body>
<main class="report">
  <section class="hero">
    <div>
      <p class="eyebrow">Prompt report card</p>
      <h1>Your Prompting Profile</h1>
      <p class="subtitle">A concise view of prompt DNA, grade signals, and next practice moves.</p>
    </div>
    <div class="overall" aria-label="Overall letter grade">
      <span class="overall-label">Overall</span>
      <strong class="overall-letter">{overall_letter}</strong>
    </div>
  </section>

  <section class="scores" aria-label="Report card scores">
    {_render_score_cards(scores)}
  </section>

  <section class="panel">
    <h2>Prompt DNA</h2>
    <div class="dna-grid">
      {_render_dna(dna)}
    </div>
  </section>

  {_render_habits(habits)}
  {_render_learning_cards(learning_cards)}
</main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render prompting profile HTML")
    parser.add_argument("--in", dest="input", type=Path, required=True, help="Profile JSON path")
    parser.add_argument("--out", type=Path, required=True, help="Report HTML path")
    args = parser.parse_args(argv)

    profile = json.loads(args.input.read_text(encoding="utf-8"))
    html_text = render_profile_html(profile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
