# Grader → Prompt Coach (Claude Code) — Design Spec

> Requirements and product design for the next major skill build. Absorbs `v2plan.md` technical decisions into a multi-flow coaching product. Claude Code only for this horizon.

**Status:** Design approved in brainstorm (2026-07-21). Awaiting user review of this written spec before implementation planning.

**Artifact readiness:** requirements / design (not an implementation plan).

---

## 1. Problem & identity

The current skill grades prompting quality (A–D) from Claude Code history. That architecture is strong, but the product still behaves like a **grader**. People return for **improvement**, not grades.

**Product identity for this build:**

- Keep the command and package name **`/grader`** (no rename).
- One skill, **multiple flows** routed by user intent.
- The grade / letter is a **side effect** of a **Prompting Profile**, not the hero.
- Teaching happens in Grade via chunked learning cards; Coach and Practice are deeper loops.

**Surfaces:** Claude Code (CLI / Code Desktop) primary. HTML artifacts open in a browser. Desktop ZIP packaging may still ship scripts, but product behavior is designed for Claude Code filesystem + local history.

---

## 2. Goals

1. Diagnose prompting habits (DNA + habits), not only emit a letter.
2. Separate **Skill** from **Efficiency** (and **Consistency**) so different behaviors are not collapsed.
3. Teach in Grade mode with chunked learning cards; offer optional practice grading.
4. Provide a distinct **Coach** flow: history baseline + live assessment + report card + coaching with in-session improvement monitoring.
5. Provide a **Practice** flow for drill-only sessions.
6. Unlock **multi-week trends** (colorful HTML charts) only after **5 completed Coach sessions**.
7. Absorb v2 technical wins: 100-prompt sample, deterministic task segmentation / efficiency, self-contained HTML.

## 3. Non-goals (this build)

- Confidence percentages per dimension
- Archetype / benchmark comparisons (“you resemble Prompt Engineer”)
- Intent taxonomy as a product surface
- Difficulty-normalized grading across all historical prompts
- Named anti-pattern brand library (Magic Prompt, etc.) as a first-class catalog
- Multi-model collectors (ChatGPT, Gemini, …)
- Cloud sync / accounts
- Multi-week trends unlocked by Grade or Practice alone
- Renaming the skill to `/coach`

---

## 4. Architecture — shared core + flow playbooks

**Approach:** Shared collector/analyzer/renderer + thin flow playbooks loaded by intent.

### 4.1 Intent router (`SKILL.md`)

| User intent (examples) | Flow | Playbook |
|------------------------|------|----------|
| “grade my prompts”, `/grader`, default assessment | **Grade** | `flows/grade.md` |
| “coach me to prompt better” | **Coach** | `flows/coach.md` |
| “I want to practice prompting” | **Practice** | `flows/practice.md` |
| “show my trends” / “multi-week progress” | **Trends** | `flows/trends.md` |

Ambiguous intent → ask one clarifying question, then route.

### 4.2 Modules

1. **Collector** — dig `~/.claude` projects (Path A) or export/paste fallback (Path B); pool newest-first to **100 prompts**; redact; truncate; task-segment.
2. **Analyzer** — Prompt DNA bars; separated Skill / Efficiency / Consistency; habit detection; Python-owned efficiency aggregates.
3. **Coach layer** — learning cards, live Coach task bank, practice packs, optional “grade my replies” loop, in-session improvement notes.
4. **Renderer** — markdown always; `render_report.py` (profile / report card); `render_trends.py` (gated charts); inline CSS/SVG only.
5. **History** — local session summaries under e.g. `~/.claude/skills/grader/history/`; Coach completion records; trends gate.

### 4.3 Relationship to `v2plan.md`

This design **absorbs** v2 rather than shipping grader-v2 then coach-v3:

| v2 decision | Disposition |
|-------------|-------------|
| `DEFAULT_PROMPT_LIMIT = 100` | Keep |
| Task segmentation + prompts-per-task efficiency in Python | Keep; Efficiency is a **separate score**, not only a letter modifier |
| Rubric transparency (per-dimension verdicts + letter derivation) | Keep; feed DNA + Skill rollup |
| Chunked report / mistake cards | Become **learning cards** in Grade |
| Self-contained HTML | Keep; extend for DNA bars, report card, trends charts |
| Hard-gate reword for conversation efficacy vs token efficiency | Keep |

---

## 5. Flow designs

### 5.1 Grade (default)

1. Collect (100-prompt dig or export).
2. Analyze → DNA, separated scores, habits, efficiency panel.
3. Report hero: **Your Prompting Profile** (DNA + Skill / Efficiency / Consistency). Overall letter secondary.
4. Rubric table: dimension | verdict | evidence (`session#/prompt#`) | what would raise it.
5. **Learning cards** (chunking): pattern → why it costs you → their example → fix / mental model.
6. Weak → stronger rewrites.
7. Coverage honesty (`prompts_sampled/100`, sessions scanned, intake path).
8. **Practice pack** (5–10 exercises targeting weakest DNA/habits) + offer to reply for same-rubric grading.
9. Render markdown + HTML when Python available.

Grade does **not** write a Coach completion record.

### 5.2 Coach

1. **History baseline** — dig + analyze (short baseline; not necessarily full Grade HTML).
2. **Live assessment** — staged tasks of **varying complexity** (easy → hard). Each task is a problem the user must address **through prompting** (craft + problem-solving fitness).
3. **Report card** — HTML preferred: history habits vs live performance; DNA / separated scores; how they did on the live set.
4. **Coaching session** — focus weakest 1–2 habits; micro-lessons; further tasks; monitor improvement **within the session** and vs prior saved Coach runs when present.
5. **Persist** — write history record with `completed: true` only if:
   - live assessment tasks finished, **and**
   - at least one coaching/practice drill round completed in that session.  
   Mid-abandon → no credit toward trends.

### 5.3 Practice

1. Dig + analyze (or equivalent diagnosis) to choose targets.
2. Present targeted exercise pack.
3. Optional: user replies → grade with same rubric.
4. Does **not** count as a Coach completion for trends.

### 5.4 Trends (gated)

- **Unlock:** ≥ **5** completed Coach sessions (see §5.2 completion rule).
- **If unlocked:** colorful self-contained HTML artifact with charts (DNA over time, efficiency, habit severity / focus) via inline SVG.
- **If locked:** deny clearly with `N/5` and what still counts as completion — no empty/misleading charts.
- Grade and Practice alone never unlock trends.

---

## 6. Scoring & profile model

### 6.1 Prompt DNA

Bars mapped to existing checklist dimensions:

1. Clarity & directness  
2. Context & motivation  
3. Success criteria  
4. Structure  
5. Constraints & boundaries  
6. Examples (when applicable)  
7. Agentic hygiene  
8. Cross-session consistency  

Per dimension: visual/text bar, Strong / Adequate / Weak / N/A, evidence cites. N/A does not lower Skill.

### 6.2 Separated scores

| Score | Meaning |
|-------|---------|
| **Skill** | Craft quality from DNA / checklist |
| **Efficiency** | Conversation efficacy: prompts-per-task, single-shot rate, rework rate (Python) |
| **Consistency** | Cross-session stability + related signals |

Someone can score high Skill and low Efficiency (excellent prompts, many revisions) or the reverse. Do not collapse Efficiency into Skill.

### 6.3 Habits

Recurring patterns with frequency and severity derived from the sample (and live Coach performance when in Coach). Prefer habits over isolated one-off mistakes in teaching priority.

### 6.4 Overall letter

Still produced (A–D) as a rollup side effect. Derivation rule documented in `checklist.md` (sub-verdicts + consistency + signals). Must not be the report hero.

### 6.5 Hard gates

- Do not use token counts, cost, spend, burn, cache, or latency as scoring inputs or primary report fields.
- Allow prompts-per-task **efficacy**; never frame it as resource/brevity reward. Terse-but-vague still grades weak.
- Cite real evidence; forbid fabricated paraphrased “evidence.”
- Keep redacted secrets redacted; do not upload transcripts to third parties.

---

## 7. Shared profile JSON contract

All flows read/write one logical profile object consumed by markdown and HTML:

- `meta` — flow id, intake path, surface, sampling counts, timestamps  
- `dna[]` — dimension, score/bar, verdict, evidence cites  
- `scores` — Skill, Efficiency, Consistency (+ short rationales)  
- `efficiency` — Python aggregates + illustrative task chain  
- `habits[]` — pattern, frequency, severity, example cites  
- `learning_cards[]` / `practice_pack[]` — teaching payloads  
- `live_assessment` — Coach-only: tasks, user prompts, notes, vs-history delta  
- `overall_letter` — rollup side effect  

LLM owns judgment fields; Python owns sampling math and efficiency aggregates.

---

## 8. Assets & packaging

| Asset | Role |
|-------|------|
| `SKILL.md` | Intent router, hard gates, shared procedure |
| `flows/grade.md`, `coach.md`, `practice.md`, `trends.md` | Flow playbooks |
| `checklist.md`, `signals.md` | Rubric + modifiers (updated for DNA / separated scores / efficacy wording) |
| `references/coach_tasks.md` (or JSON) | Live assessment task bank by complexity |
| `scripts/grader_lib.py` | Collector + segmentation + efficiency + history helpers |
| `scripts/render_report.py` | Profile / report card HTML |
| `scripts/render_trends.py` | Trends HTML (gate enforced in skill + script) |
| Local `history/` | Coach completion summaries (aggregates; no secret leakage) |

`package_for_desktop.py` should include new scripts/flows when zipping; primary UX remains Claude Code.

---

## 9. History record (minimum fields)

Each completed Coach session appends approximately:

- `id`, `completed_at`  
- `completed: true`  
- DNA snapshot scores  
- Skill / Efficiency / Consistency  
- habits_focus[]  
- live_assessment summary scores  
- optional notes for in-session improvement  

Incomplete runs may be logged as `completed: false` for debugging but **must not** increment the trends unlock counter.

---

## 10. Success criteria

- User can run Grade and receive a Profile-first report with DNA, separated scores, habits, learning cards, and practice offer.
- User can run Coach through live assessment → report card → coaching drills; completion persists when rules met.
- User can run Practice without a full Coach arc.
- Trends denies at 4 completed Coach sessions and unlocks at 5 with chart HTML.
- Efficiency never appears as token/cost scoring; Skill and Efficiency remain distinct.
- Pytest covers: prompt cap 100, segmentation/efficiency math, completion counting, trends gate, self-contained HTML (no external network asset refs).

---

## 11. Open implementation details (for planning, not blockers)

- Exact on-disk history path and file format (JSONL vs JSON files).
- Number of live Coach assessment tasks per complexity band (suggest 1–2 easy, 2 medium, 1 hard — finalize in plan).
- Whether Path B (export/paste) can write history on non-Code surfaces (default: history is Claude Code–local only).
- Visual design system for HTML (load artifact-design / dataviz guidance at implementation time).

---

## 12. Settled decisions log

| Topic | Decision |
|-------|----------|
| Horizon | Claude Code skill; coach-in-skill |
| vs v2 | Absorb into this design |
| Name | Keep `/grader` |
| Structure | Shared core + flow playbooks |
| Grade features | DNA, separated scores, habits, learning cards, practice pack + optional loop |
| Practice depth | Pack + optional grade-replies |
| Coach assessment source | Hybrid: history dig + live tasks |
| Coach arc | Live tasks → report card → coach + monitor improvement |
| Trends | HTML charts; unlock at **5** completed Coach sessions |
| Completion | Live assessment finished + ≥1 coaching/practice drill round |
| Deferred | Confidence, archetypes, anti-pattern catalog, multi-model, cloud |
