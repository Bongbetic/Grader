# Structured Plan — Grader v2 (transparency, chunking, efficiency, visual)

> Planning document only. No implementation changes are described as done here — this is the agreed blueprint before execution.

## How the skill works today

**Two layers:**

1. **Deterministic layer (Python, `scripts/grader_lib.py`)** — builds a "dossier" JSON. It does *no grading*. It only:
   - **Path A:** digs `~/.claude/projects/**/*.jsonl`, ranks sessions by mtime, takes the top `DEFAULT_SESSION_LIMIT = 30`, extracts **user prompts only** (filters tool/assistant turns), redacts secrets, truncates prompts >4000 chars.
   - **Path B:** parses a pasted `/export` or transcript into the same shape.
   - Computes 4 lightweight `signals` per session: `corrections`, `restates` (Jaccard ≥0.8 vs prev), `clarify_loops`, `abandoned_goal`.

2. **Judgment layer (the LLM, driven by `SKILL.md`)** — reads `checklist.md` (8 craft dimensions + A–D scale) and `signals.md` (light modifiers), scores the dossier, and emits an 8-section markdown report. Grading is entirely LLM reasoning; scripts never assign a grade.

**Key files:** `SKILL.md` (procedure + hard gates), `checklist.md` (rubric), `signals.md` (modifiers + forbidden metrics: tokens/cost/latency/"efficiency" framed on resources), `references/best-practices-policy.md`, `scripts/package_for_desktop.py` (builds `grader.zip`), plus `tests/` and `fixtures/`.

**Two surfaces:** Claude Code CLI (terminal, no artifact rendering) and Claude Desktop/claude.ai (renders HTML artifacts, has code execution).

## Design decisions locked in
- **Sample unit = 100 prompts**, pooled across *all* discovered sessions (newest-first), not 100 sessions. New knob: `DEFAULT_PROMPT_LIMIT = 100`. `DEFAULT_SESSION_LIMIT` becomes a safety ceiling on how many session files to scan (raised, e.g. to 100) but the graded sample is bounded to 100 prompts. Launched from a fresh Claude Code session, the skill assesses 100 prompts pooled from all sessions.
- **Visual output = one self-contained `.html` file** (inlined CSS, no external assets), openable in a browser on any surface and renderable as an inline Artifact on Desktop.
- **Efficiency = prompts-per-task (conversation efficacy)**, explicitly *not* token/cost. Hard-gate wording gets tightened, not loosened.

## Tension flagged
The efficiency metric ("how many prompts to accomplish a task") collides with an existing hard gate. `signals.md` forbids "*Model-tier comparisons framed as efficiency*" and "*any metric that rewards brevity*." The ask is legitimately different — it is **conversation efficacy** (prompts-per-task), *not* token/cost efficiency, which the skill already measures indirectly via corrections/restates. Plan treats prompts-per-task as an efficacy metric and rewords the gate to forbid only *resource/token* efficiency, keeping the wall against cost-scoring intact.

---

## 1. Data layer — `scripts/grader_lib.py`

**1a. Prompt-capped pooling**
- Add `DEFAULT_PROMPT_LIMIT = 100`.
- `build_dossier_from_claude_root(root, session_limit, prompt_limit=100)`: iterate sessions newest-first, accumulate prompts, **stop once 100 prompts collected** (last session may be partially included; record `prompts_sampled` and `prompts_available`).
- Dossier gains: `prompts_sampled`, `prompts_available`, `sessions_scanned`. Coverage reporting shifts from `sessions_graded/30` → `prompts_sampled/100` (plus session count for context).

**1b. Task segmentation + efficiency metric (new)**
- `segment_tasks(user_prompts)` → groups consecutive prompts into "tasks" using topic-continuity: Jaccard token overlap between adjacent prompts (continuation if overlap ≥ threshold OR a correction/restate), new task on a low-overlap topic shift. Reuses `_tokens`/`_jaccard`. Default threshold ~0.3, exposed as a constant.
- `compute_efficiency(tasks)` → per-task `{prompt_count, corrections, restates, resolved}` and aggregate `prompts_per_task` (mean/median), `single_shot_rate` (tasks done in 1 prompt), `rework_rate` (tasks with ≥1 correction/restate).
- Store under `dossier["efficiency"]`. **Deterministic in Python** so the LLM interprets rather than recomputes.
- Efficiency feeds the existing signal modifiers; it does **not** invent a new letter axis (avoids double-counting friction).

**1c. Per-dimension scaffolding for transparency**
- Optionally emit a lightweight `evidence_index` (dimension → candidate prompt indices) so the rubric table can cite `session/prompt` cheaply. Hints, not scoring.

## 2. Rubric transparency — `checklist.md` + `SKILL.md`
- Add an explicit **per-dimension scoring scale** (Strong / Adequate / Weak / N/A) so each of the 8 dimensions gets a visible sub-verdict — makes the grade traceable, not opaque.
- Define the **letter derivation rule** in words (how sub-verdicts + consistency + signals roll up to A–D) so "why this grade" is mechanical.
- Rubric-doc edits only; grading stays LLM-driven.

## 3. Output redesign — `SKILL.md` report template
Replace the 8-section flat markdown with a chunked, learn-from-mistakes structure:

1. **Grade + one-line rationale** (concise "why this grade").
2. **Rubric table** — one row per dimension: `Dimension | Verdict | Evidence snippet | What would raise it`. The transparent "exactly how you were graded."
3. **Efficiency panel** — prompts-per-task, single-shot rate, rework rate, worst-offending task with its prompt chain.
4. **Mistake chunks** — each recurring gap as a self-contained learning card: *pattern → why it costs you → your example → the fix*.
5. **Weak → stronger rewrites** (kept, grounded in their prompts).
6. **Coverage** (`prompts_sampled/100`, sessions scanned, intake path, surface).

## 4. Visual artifact — new `scripts/render_report.py`
- Input: a small JSON the LLM produces (grade, per-dimension verdicts + evidence, efficiency numbers, mistake chunks).
- Output: **one self-contained `.html`** — rubric as a color-coded table, grade badge, efficiency bar/gauge (inline SVG, no libraries), theme-aware (light/dark). No external fonts/CDN so it satisfies artifact CSP and works offline.
- `SKILL.md` gains a step: after grading, write the JSON → run `render_report.py` → on Desktop present as Artifact, on CLI report the file path. Falls back to the markdown table if Python is unavailable.
- Design: load the `dataviz` and `artifact-design` skills before writing the HTML so the visual reads as a coherent, accessible system.

## 5. Hard-gate rewording — `signals.md` + `SKILL.md`
- Keep forbidding **token/cost/latency/cache** as grading inputs.
- Add an explicit **allow** for prompts-per-task efficacy, noting it must never be framed as a resource/brevity metric (a terse-but-vague prompt still grades weak — reinforces existing "never inflate / never reward brevity" rule).

## 6. Tests — `tests/`
- Update `test_default_session_limit_is_30` and add `test_default_prompt_limit_is_100`.
- New tests: prompt-cap pooling stops at 100; `segment_tasks` splits on topic shift & merges corrections; `compute_efficiency` math; `render_report.py` produces valid self-contained HTML (no `http`/`src=` external refs).
- Keep all existing redaction/truncation/CLI tests green.

## 7. Packaging
- `package_for_desktop.py` already globs the whole skill dir, so `render_report.py` ships automatically. Verify the zip includes it; no code change likely needed.

---

## Suggestions: quality improvements
- **Determinism where it's cheap:** task-segmentation + efficiency fully in Python so results are reproducible and don't drift per run.
- **Evidence integrity:** require every rubric row to cite a real `session#/prompt#`; forbid paraphrased "evidence." Cuts fabrication risk.
- **Sampling honesty:** with a 100-prompt newest-first cap, report explicitly what was excluded so a low grade cannot hide behind sampling.
- **Confidence flag:** when `prompts_sampled` is small (<20), down-weight cross-session consistency claims rather than overclaiming.
- **Calibration fixtures:** add a mid-grade (B/C boundary) fixture and a high-rework/low-craft fixture so the efficiency↔craft interaction is regression-tested, not just strong/weak extremes.

## Suggestions: token efficiency
- **Lazy-load references:** `SKILL.md` front-loads reading `checklist.md` + `signals.md` + policy every run. Read `signals.md` and `best-practices-policy.md` only when relevant (signals present / user attached a doc). Biggest single saving.
- **Precompute, don't re-read:** efficiency + segmentation in Python means the LLM ingests small aggregates, not raw math over 100 prompts.
- **Cap evidence quoting:** snippets ≤ ~120 chars (add a display cap alongside the existing 4000-char storage truncation).
- **Single structured hand-off:** the LLM emits one compact grading-JSON that *both* the markdown report and `render_report.py` consume — no double authoring.
- **Trim the dossier context:** keep `_redaction_notes` / raw timestamps in the file for the renderer, not in the model's context.

---

## Risks / things to watch
- **Partial last session** when hitting the 100-prompt cap — must not corrupt cross-session consistency scoring (mark it partial).
- **CLI can't render artifacts** — HTML is written to disk and the path is surfaced; agreed fallback.
- **Scope of `signals.md` gate reword** — keep the cost/token wall intact and only carve out prompts-per-task; can leave wording untouched if preferred.

## Verification before push
`pip install -r requirements.txt && python -m pytest -v`, build the zip, and generate the HTML against the `strong`/`weak` fixtures to eyeball the visual — all on branch `claude/skill-grading-transparency-f4og5p`.

## Open toggles
- Whether to reword the `signals.md` hard gate (§5) or leave it verbatim.
- Task-segmentation Jaccard threshold (default ~0.3, exposed as a constant).
