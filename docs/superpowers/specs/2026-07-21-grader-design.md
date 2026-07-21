# Grader — Design Spec

**Date:** 2026-07-21  
**Status:** Approved for planning  
**Delivery:** Claude Code skill named `grader`  
**Approach:** Skill + compact extractor (auto-dig) with export/paste fallback

## Problem

People use Claude Code heavily but get little structured feedback on *how* they prompt. Existing materials (Anthropic best-practices docs, Heimdall optimizer grading) target writing or refining a single prompt — not assessing a person’s recent prompting habits from real local session history.

We need a local grader that:

1. Digs recent Claude Code user prompts from this machine (last 30 sessions by default).
2. Scores them against a distilled checklist of prompting best practices.
3. Incorporates light conversation-efficacy signals (corrections, restates, abandon patterns).
4. Returns one definitive letter grade (A–D) plus structured improvement feedback, including inconsistency callouts.
5. Falls back to `/export` or pasted transcripts when automatic digging fails.

Explicit non-goals: token/cost “burn” metrics, Cursor/Codex adapters in v1, live prompt-rewriter product, trend dashboards.

## Goals & success criteria

**Goals**

- Package as a Claude Code skill: `grader`.
- Prefer automatic harness digging of local Claude Code history.
- Always offer a fallback intake path that feeds the same grading pipeline.
- Grade against a **distilled** Claude Code user-prompt checklist derived from `Best prompting Practices.md` (full doc is reference-only).
- Output a single overall **A–D** grade for the sampled history plus actionable structured feedback.

**Success looks like**

- Invoking `grader` on a machine with Claude Code history produces a dossier from the last 30 sessions and an A–D report without manual export.
- When dig fails (missing dir, parse drift, empty history), the skill clearly switches to Path B and still grades.
- Two runs on the same fixture set produce the same letter and the same primary gap themes.
- Report always includes: letter, evidence snippets, inconsistency notes (or “none”), and 3–5 concrete improvement actions.

## Scope

### In scope (v1)

- Claude Code skill `grader`
- Extractor for `%USERPROFILE%\.claude` / `~/.claude` (honor `CLAUDE_CONFIG_DIR`)
- Last **30** sessions by default (file mtime across projects)
- Compact dossier schema shared by auto-dig and fallback
- Distilled `checklist.md` + `signals.md`
- A–D overall grade + structured feedback report
- Local-only processing; basic secret redaction in dossier/report

### Out of scope (v1)

- Cursor Desktop/CLI and Codex Desktop/CLI adapters
- Token, cost, latency, or spend scoring
- Multi-user / team benchmarking
- Persistent analytics DB or charts
- Automatic rewriting of the user’s future prompts (feedback only)

### Deferred

- Additional harness adapters reusing the same dossier + checklist
- Configurable N / time-window overrides at invoke time
- Optional save of reports into a standard project path

## Architecture

```text
Invoke grader (Claude Code skill)
        │
        ├─ Path A (preferred): Extractor digs Claude Code JSONL sessions
        │                      → last 30 by mtime
        │                      → compact dossier
        │
        └─ Path B (fallback):  /export or pasted transcripts
                               → same dossier shape
        │
        ▼
   Grader (SKILL.md procedure + checklist.md + signals.md)
        │
        ▼
   Report: A–D + structured feedback (local)
```

**Design principle:** one grading brain, two intake paths. Extraction differences must not change the rubric or report schema.

## Components

### 1. Skill entrypoint — `SKILL.md`

- Triggers: user wants to grade prompting quality / review recent Claude Code prompting habits / run `grader`.
- Procedure: attempt Path A → on failure Path B → grade → emit report.
- Hard rules: no token/cost metrics; N/A checklist items excluded; cite evidence from the sample; one overall letter.

### 2. Extractor (Path A)

- Resolve config root: `CLAUDE_CONFIG_DIR` else `~/.claude` / `%USERPROFILE%\.claude`.
- Discover session transcripts under `projects/**` (JSONL; layout may be `*.jsonl` directly under project dirs or under `sessions/` — support both).
- Select the **30 most recent** session files by mtime (lexicographic ULID order as secondary tie-break when available).
- Emit a compact **dossier** (JSON or Markdown summary). Do **not** dump full assistant/tool payloads into the grader context.

**Dossier fields (per session)**

| Field | Purpose |
|-------|---------|
| `session_id` | Identity |
| `project_path` | Encoded/decoded project path if available |
| `started_at` / `ended_at` | Ordering & coverage |
| `user_prompts[]` | Ordered user text only |
| `signals` | Heuristic tags/counts (see signals) |
| `prompt_count` | Weighting / coverage |

**Aggregation header:** `sessions_found`, `sessions_graded` (e.g. `18/30`), `intake_path` (`auto` \| `export` \| `paste`), redaction notes.

### 3. Fallback normalizer (Path B)

- Accept Claude Code `/export` markdown or pasted user/assistant turns.
- Map into the same dossier schema.
- If coverage < 30, grade available set and report `n/30`.

### 4. Checklist — `checklist.md`

Distilled from the user’s Claude best-practices document for **historical user prompts in Claude Code** (not API system-prompt engineering). Dimensions:

1. **Clarity & directness** — explicit ask; unambiguous outcome  
2. **Context & motivation** — why constraints exist when it matters  
3. **Success criteria** — what “done” means  
4. **Structure** — steps when order matters; instructions separated from data  
5. **Constraints & boundaries** — scope, must/must-not, safety/agentic limits  
6. **Examples** — when format/judgment consistency matters  
7. **Agentic hygiene** — proportionate scope; avoid over-eager / test-gaming instructions; state boundaries for long runs  
8. **Cross-session consistency** — stable constraints/style; flag contradictory habits without reason  

Items may be marked **N/A** for a given sample; N/A never lowers the grade.

The full `Best prompting Practices.md` may be bundled or linked as **reference-only**. It is not scored line-by-line.

### 5. Signals — `signals.md`

**Allowed efficacy hints (modifiers, not sole grade basis):**

- Repeated user corrections of the same misunderstanding  
- Restating the same ask with little new information  
- Clarify loops (assistant asks → user still vague → repeat)  
- Abandoned goals (task dropped mid-thread without resolution)

**Forbidden:** token counts, cost, cache stats, latency, model pricing, “burn” narratives.

Signal modifiers may pull a letter down one step when strong and corroborated by craft gaps (e.g. A→B, B→C). They must not invent a D from signals alone.

### 6. Report

Required sections:

1. **Overall grade** — single letter A–D  
2. **Coverage** — `sessions_graded/30`, intake path  
3. **Evidence** — short anonymized prompt snippets supporting the grade  
4. **Strengths** — 2–4 bullets  
5. **Gaps** — checklist dimensions missed, with examples  
6. **Inconsistencies** — contradictions across the sample, or explicit “none found”  
7. **Improve next** — 3–5 concrete actions  
8. **Weak → stronger** — 2–3 rewritten examples grounded in their actual prompts  

Optional: write report markdown into the current working project if the user asks; default is display in-session.

## Grading scale

Applies to the **aggregate** of the sampled sessions (default last 30), not a single prompt.

| Grade | Meaning |
|-------|---------|
| **A** | Consistently clear, contextualized, well-scoped prompts; few correction/restatement loops; applicable checklist mostly satisfied; no material cross-session contradictions |
| **B** | Strong overall; recurring soft spots (e.g. missing success criteria, uneven structure) or mild inconsistency; some clarify/correct loops |
| **C** | Frequent vagueness, missing constraints/context, or clear craft↔signal mismatch (weak prompts *and* heavy correction loops) |
| **D** | Habitual under-specification or contradictory prompting; signals show repeated failure to steer; foundational gaps dominate |

**Decision order**

1. Score applicable checklist dimensions on the dossier.  
2. Apply consistency assessment (contradictory habits without reason → note and possibly cap).  
3. Apply signal modifiers lightly.  
4. Emit one letter + evidence. Never inflate: polish does not raise a grade built on chronic under-specification.

## Data flow

1. User invokes `grader` inside Claude Code.  
2. Skill runs extractor against local Claude Code storage.  
3. On success → dossier (`intake_path: auto`).  
4. On failure → instruct `/export` or paste → normalize → dossier.  
5. Grader reads dossier + checklist + signals.  
6. Emit structured A–D report locally.

## Error handling

| Condition | Behavior |
|-----------|----------|
| Missing config dir / no projects | Explain; Path B only |
| JSONL parse / schema drift | Fail dig gracefully; Path B (`/export`) |
| 0 sessions | Cannot grade craft history; ask for export/paste |
| 1–29 sessions | Grade available; report `n/30` coverage |
| Suspected secrets in prompts | Redact before dossier/report (API key-like patterns, private tokens) |
| Huge prompts | Truncate in dossier with length note; grade on visible craft patterns |

## Privacy

- All processing is local to the user’s machine and Claude Code session.  
- Do not instruct uploading transcripts to third parties.  
- Redact obvious secrets in artifacts the skill writes.

## Testing

- **Fixtures:** synthetic JSONL sessions + `/export` markdown samples covering strong, weak, and inconsistent prompting.  
- **Extractor:** stable dossier schema; correct “last 30” selection; graceful failure when path missing.  
- **Grader:** same fixtures → stable letter and expected primary gap themes.  
- **Fallback:** export/paste → same schema → comparable grade on equivalent content.  
- **Signals:** fixture with heavy correction loops lowers letter only when craft gaps also present (document expected cases).

## File layout (skill package)

```text
grader/
  SKILL.md           # entry, procedure, report template, hard gates
  checklist.md       # distilled rubric
  signals.md         # allowed/forbidden efficacy signals
  scripts/           # extractor (compact dossier emitter)
  references/        # optional: best-practices pointer or excerpt policy
  fixtures/          # test transcripts / expected grade themes
```

Exact install path follows Claude Code skill conventions at implementation time (user or project skill directory).

## v1 acceptance checklist

- [ ] Skill named `grader` invocable in Claude Code  
- [ ] Auto-dig of last 30 local sessions when history exists  
- [ ] Fallback to export/paste with identical dossier schema  
- [ ] Distilled checklist used for scoring; full best-practices doc not line-scored  
- [ ] Single A–D overall grade  
- [ ] Structured feedback includes inconsistencies + improve-next + weak→stronger examples  
- [ ] No token/cost metrics anywhere in procedure or report  
- [ ] Fixture-based verification of extractor + grade stability  

## Open decisions (resolved)

| Topic | Decision |
|-------|----------|
| Unit of analysis | Last 30 sessions from Claude Code local history |
| Harness (v1) | Claude Code only |
| Delivery | Claude Code skill |
| Score form | Letter A–D only |
| Rubric | Distill checklist from best-practices doc |
| Efficacy | Craft + light conversation signals |
| Architecture | Approach 2 — extractor + shared grader |
| Skill name | `grader` |
