"""Seam: render_grade_html — finalized report dict → contracted Tri-pane HTML."""
from __future__ import annotations

from render_grade_html import render_grade_html


def _available_report(**overrides):
    base = {
        "id": "rid",
        "prompt_id": "p-42",
        "percent": 87.2,
        "band": "C",
        "band_raw": "B",
        "modifier_reason": "efficacy:user_under_specified",
        "confidence": "low",
        "caps_applied": [],
        "dimension_scores": [
            {"dimension_id": "D1", "level": 3, "weight": 3},
            {"dimension_id": "D2", "level": 2, "weight": 2},
            {"dimension_id": "D5", "level": "N/A", "weight": 3},
        ],
        "rationales": {
            "D1": "Clear objective + checkable done.",
            "D2": "Background present; motivation thin.",
            "D5": "Model class unknown — excluded from denominator.",
        },
        "efficacy": {
            "status": "available",
            "session_id": "s1",
            "prompts_per_task_mean": 3.2,
            "single_shot_rate": 0.25,
            "attributed_rework_rate": 0.5,
            "worst_task_prompt_count": 4,
            "restates": 2,
            "corrections": 1,
            "abandoned_goal": False,
        },
        "planning": {
            "status": "available",
            "session_id": "s1",
            "planned_decomposition": 1,
            "additive_feature": 0,
            "adaptive_change_with_evidence": 0,
            "scope_change_without_prior_signal": 1,
            "under_specified_initial_plan": 1,
        },
        "excerpt": "do NOT write any code, just report…",
        "classification_summary": {
            "prompt_class": "structured_dispatch",
            "task_complexity": "moderate",
            "rework_cause": "user_under_specified",
        },
    }
    base.update(overrides)
    return base


GOLDEN_AVAILABLE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Grade report · p-42</title>
<style>
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
</style>
</head>
<body>
<article class="grade-report" data-prompt-id="p-42">
<header class="topbar" data-region="topbar">
<div>
<div class="meta-muted">p-42</div>
<div>Craft <span class="band-letter">C</span> <span class="meta-muted">raw B · ~87.2% · confidence low</span></div>
<div class="meta-muted">modifier: efficacy:user_under_specified</div>
</div>
<aside class="security-ok" data-region="security">none detected</aside>
</header>
<div class="panes">
<section class="pane" data-region="craft">
<h2>Craft</h2>
<p class="metric">C</p>
<p class="meta-muted">excerpt: do NOT write any code, just report…</p>
<p class="meta-muted">caps: none</p>
</section>
<section class="pane" data-region="efficacy">
<h2>Efficacy</h2>
<p class="metric">attributed rework: 50%</p>
<p class="meta-muted">restates 2 · corrections 1 · prompts/task 3.2 · single_shot 0.25 · worst 4 · abandoned_goal false</p>
<p>attribution: 2 restates attributed to under-specified opener — not agent misread.</p>
</section>
<section class="pane" data-region="planning">
<h2>Planning</h2>
<ul>
<li>planned_decomposition: 1</li>
<li>under_specified_initial_plan: 1</li>
<li>scope_change_without_prior_signal: 1</li>
<li>additive_feature: 0</li>
<li>adaptive_change_with_evidence: 0</li>
</ul>
<p class="meta-muted">callouts:</p>
<ul class="callouts">
<li>planned_decomposition ×1</li>
<li>under_specified_initial_plan ×1</li>
<li>scope_change_without_prior_signal ×1</li>
</ul>
</section>
</div>
<section class="dims" data-region="dimensions">
<div class="meta-muted">Dimensions</div>
<div class="dim-chips">
<span class="chip">D1 3</span>
<span class="chip">D2 2</span>
<span class="chip na">D5 N/A</span>
</div>
<details class="rationale"><summary>D1</summary>Clear objective + checkable done.</details>
<details class="rationale"><summary>D2</summary>Background present; motivation thin.</details>
<details class="rationale"><summary>D5</summary>Model class unknown — excluded from denominator.</details>
</section>
<section class="coaching" data-region="coaching">
<div class="slot-box"><h3>Strongest</h3><p class="hint">_(empty — fill &lt;=120 chars)_</p></div>
<div class="slot-box"><h3>Weakest</h3><p class="hint">_(empty — fill &lt;=120 chars)_</p></div>
<div class="slot-box"><h3>Next actions</h3><ol class="actions"><li class="hint">_(empty — fill &lt;=80 chars)_</li><li class="hint">_(empty — fill &lt;=80 chars)_</li><li class="hint">_(empty — fill &lt;=80 chars)_</li></ol></div>
</section>
</article>
</body>
</html>
"""


def test_available_axes_golden():
    assert render_grade_html(_available_report()) == GOLDEN_AVAILABLE


GOLDEN_UNAVAILABLE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Grade report · p-1</title>
<style>
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
</style>
</head>
<body>
<article class="grade-report" data-prompt-id="p-1">
<header class="topbar" data-region="topbar">
<div>
<div class="meta-muted">p-1</div>
<div>Craft <span class="band-letter">A</span> <span class="meta-muted">raw A · ~91.7% · confidence uncalibrated</span></div>
<div class="meta-muted">modifier: no_change</div>
</div>
<aside class="security-ok" data-region="security">none detected</aside>
</header>
<div class="panes">
<section class="pane" data-region="craft">
<h2>Craft</h2>
<p class="metric">A</p>
<p class="meta-muted">excerpt: _(none)_</p>
<p class="meta-muted">caps: none</p>
</section>
<section class="pane" data-region="efficacy">
<h2>Efficacy</h2>
<p>unavailable — no session context</p>
</section>
<section class="pane" data-region="planning">
<h2>Planning</h2>
<p>unavailable — no session context</p>
</section>
</div>
<section class="dims" data-region="dimensions">
<div class="meta-muted">Dimensions</div>
<div class="dim-chips">
<span class="chip">D1 3</span>
</div>
<details class="rationale"><summary>D1</summary>ok</details>
</section>
<section class="coaching" data-region="coaching">
<div class="slot-box"><h3>Strongest</h3><p class="hint">_(empty — fill &lt;=120 chars)_</p></div>
<div class="slot-box"><h3>Weakest</h3><p class="hint">_(empty — fill &lt;=120 chars)_</p></div>
<div class="slot-box"><h3>Next actions</h3><ol class="actions"><li class="hint">_(empty — fill &lt;=80 chars)_</li><li class="hint">_(empty — fill &lt;=80 chars)_</li><li class="hint">_(empty — fill &lt;=80 chars)_</li></ol></div>
</section>
</article>
</body>
</html>
"""


def test_unavailable_axes_golden():
    report = {
        "prompt_id": "p-1",
        "percent": 91.7,
        "band": "A",
        "band_raw": "A",
        "modifier_reason": "no_change",
        "confidence": "uncalibrated",
        "caps_applied": [],
        "dimension_scores": [{"dimension_id": "D1", "level": 3, "weight": 3}],
        "rationales": {"D1": "ok"},
        "efficacy": {"status": "unavailable", "reason": "no session context"},
        "planning": {"status": "unavailable", "reason": "no session context"},
    }
    assert render_grade_html(report) == GOLDEN_UNAVAILABLE


def test_caps_listed_under_craft():
    out = render_grade_html(
        _available_report(caps_applied=["forced_cot_on_reasoning", "internal_contradiction"])
    )
    assert "caps: forced_cot_on_reasoning, internal_contradiction" in out
    assert 'data-region="craft"' in out


def test_security_hit_in_topbar():
    out = render_grade_html(
        _available_report(
            security={
                "status": "hit",
                "severity": "high",
                "summary": "1 secret-shaped token matched.",
                "action": "Rotate referenced credential.",
            }
        )
    )
    assert 'class="security-hit" data-region="security"' in out
    assert "severity: high" in out
    assert "1 secret-shaped token matched." in out
    assert "action: Rotate referenced credential." in out


def test_coaching_slots_filled_and_truncated():
    strong = "S" * 150
    weak = "W" * 150
    actions = ["A" * 100, "B" * 100, "C" * 100, "D" * 100]
    out = render_grade_html(
        _available_report(
            slots={
                "strongest": strong,
                "weakest": {"text": weak},
                "next_actions": actions,
            }
        )
    )
    assert f"<p>{'S' * 120}</p>" in out
    assert f"<p>{'W' * 120}</p>" in out
    assert f"<li>{'A' * 80}</li>" in out
    assert f"<li>{'B' * 80}</li>" in out
    assert f"<li>{'C' * 80}</li>" in out
    assert "D" * 80 not in out
    coaching = out.split('data-region="coaching"', 1)[1]
    assert coaching.count("<li>") == 3


def test_cli_renders_report_json(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path as P

    root = P(__file__).resolve().parents[1]
    cli = root / "skills" / "grader" / "scripts" / "render_grade_html.py"
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_available_report()), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(cli), "--report", str(report_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == GOLDEN_AVAILABLE


def test_agent_misread_attribution():
    out = render_grade_html(
        _available_report(
            classification_summary={
                "prompt_class": "standalone",
                "task_complexity": "simple",
                "rework_cause": "agent_misread",
            }
        )
    )
    assert "attribution: 2 restates — agent misread, not your prompt." in out


def test_html_escapes_excerpt():
    out = render_grade_html(_available_report(excerpt='<script>alert("x")</script>'))
    assert "<script>" not in out
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in out
