---
name: grader
description: >
  Prompt-learning coach for engineering students who ship with AI dev tools. Grades
  a single prompt against an 11-dimension research rubric (D1–D11), coaches rewrites,
  runs practice drills, and shows local trends. Use for /grader, "grade my prompt",
  "coach me to prompt better", "practice prompting", or "show my trends". No token/cost metrics.
disable-model-invocation: false
---

# Grader — Prompt-learning coach for AI dev tools

Runs on **any supported coding agent**: **Claude Code**, **Cursor**, **OpenAI Codex CLI**, or **GitHub Copilot** (skills). Also works on **Claude Desktop / claude.ai** via uploaded ZIP with code execution. Keep the skill name `/grader` (or invoke with natural language).

**You are the judge.** The agent reading this skill — the one the Learner is talking to right now — scores prompts. There is no separate judge API. Return dimension levels, N/A marks, rationales, and disqualifier flags as JSON; Python always recomputes percent, band, and caps via `scripts/finalize_grade.py`.

Audience: engineering students who ship real side-projects with Claude Code, Cursor, Copilot, Codex, or ChatGPT. The goal is durable prompting skill, not a scoreboard.

## Hard gates

- No token/cost metrics. Do not use token counts, cost, spend, cache, model tier, or latency as grading inputs or report fields.
- Grade against the 11-dimension rubric in `references/rubric-sheet.md` (D1–D11). Retire the v2 Prompt-DNA / checklist path.
- Hybrid scoring: **you** (the current agent) return dimension levels, N/A marks, rationales, and disqualifier flags as JSON; Python always recomputes percent, band, and caps via `scripts/finalize_grade.py`.
- **Judge consistency:** learner-facing grades require **host-LLM judge JSON per prompt** — no heuristic batch substitute. Deterministic math/render is host-model-independent; dimension levels are not guaranteed identical across judging models. See `references/judge-consistency.md`.
- Consent first. Auto-discover reads only allowlisted local tool-history paths after the user grants per-tool consent. Show a scan summary and wait for the user to proceed before grading.
- Grade-then-discard by default: persist scores, redacted excerpt, and metadata; store raw text only on opt-in. Secrets and emails are redacted before any transmit or storage.
- Do not upload transcripts to third parties.
- Emit exactly one overall letter grade: A, B, C, or D. Pair it with the computed percentage textually.
- Four flows only: `flows/grade.md`, `flows/coach.md`, `flows/practice.md`, `flows/trends.md`.

## 11-dimension rubric

| ID | Dimension | Weight | Kind |
|---|---|---|---|
| D1 | Objective & Success Criteria | ×3 | Core |
| D2 | Context & Motivation | ×2 | Core |
| D3 | Specificity & Constraints | ×2 | Core |
| D4 | Output Format & Structure | ×2 | Core |
| D5 | Model & Parameter Fit | ×3 | Core |
| D6 | Economy & Clarity | ×2 | Core |
| D7 | Testability & Iteration-Readiness | ×2 | Core |
| D8 | Grounding / Reference Material | ×3 | Conditional |
| D9 | Examples / Shot Design | ×2 | Conditional |
| D10 | Voice: Persona / Style / Tone / Audience | ×2 | Conditional |
| D11 | Hallucination / Safety Guards | ×2 | Conditional |

Conditional dimensions (D8–D11) are marked **N/A** when the task does not trigger them. `score_math.finalize` drops N/A dimensions from the denominator. When `target_model_class` is `unknown`, it also excludes D5 from the denominator (AS-005) — not a level-1 cap.

## Intent router

After determining the user's intent, read the matching `flows/*.md` file and follow it.

| Intent | User language | Flow file | Notes |
|--------|---------------|-----------|-------|
| Grade (default) | `/grader`, "grade my prompt", "run grader", ambiguous grader request | `flows/grade.md` | Per-prompt grade; no coach history credit. |
| Coach | "coach me", "train me", "live assessment", "help me improve prompting" | `flows/coach.md` | Baseline + live tasks + teaching fixes. |
| Practice | "practice prompting", "give me exercises", "drill me" | `flows/practice.md` | No history credit. |
| Trends | "show my trends", "progress", "history" | `flows/trends.md` | From persisted grades + metrics. |

When multiple intents appear, prefer the most specific active request: Trends > Coach > Practice > Grade.

## Shared intake procedure

### 1. Check consent

Auto-discovery requires a per-tool grant. Check with `scripts/consent.py` / `scripts/scan_intake.py` or call `consent.has_consent(tool)` from `scripts/consent.py`. If no grant exists, ask the user before reading any tool history. Grant quickly from the skill directory with:

```bash
python3 scripts/grant_consent.py --tool claude
```

### 2. Scan or import

From this skill directory, run an allowlisted scan:

```bash
python3 scripts/scan_intake.py --tools claude --json
# Optional: --limit 50 caps recent session files scanned per tool (default 100)
```

**Windows shell:** default PowerShell 5.1 does not support `&&`. Chain commands with `;` instead, or use PowerShell 7+ where `&&` works.

```powershell
# PowerShell 5.1
cd $HOME\.cursor\skills\grader; python scripts/scan_intake.py --tools cursor --json

# PowerShell 7+
cd $HOME\.cursor\skills\grader && python scripts/scan_intake.py --tools cursor --json
```

Supported tools: `claude`, `codex`, `cursor`, `copilot`. For server-side tools or pasted prompts, use `adapters/import_paste.py` or the import/paste path in `flows/grade.md`.

**Cursor manual export (optional):** when auto-discovery misses transcripts, copy exported Cursor chat `.jsonl` files into `~/.cursor/grader-import/` and scan again. Grader reads that folder in addition to `~/.cursor/projects/**/agent-transcripts/`.

### 3. Show the summary and wait for proceed

`scan_intake.py` prints a JSON summary: tool, candidate count, session limit vs corpus (`sessions_found`, `sessions_scanned`, `prompts_discovered`, `prompts_in_scan`), time range, redaction count, and `protocol_reply_excluded` (workflow gate replies dropped by the shared sanitizer). Present it to the user and grade only after they confirm.

### 4. Follow the selected flow

After the user proceeds, read the matching flow playbook:

- `flows/grade.md`
- `flows/coach.md`
- `flows/practice.md`
- `flows/trends.md`

## Install (any host)

From the repo root or this skill directory:

```bash
python3 scripts/install_skill.py --host auto
```

Hosts: `claude`, `cursor`, `codex`, `copilot`, or `all`. Auto-detect uses environment signals; if detection fails, pass `--host` explicitly.

| Host | Skill path |
|------|------------|
| Claude Code | `~/.claude/skills/grader` |
| Cursor | `~/.cursor/skills/grader` |
| Codex CLI | `~/.codex/skills/grader` and `~/.agents/skills/grader` |
| GitHub Copilot | `~/.github/skills/grader` |

## Key scripts

- `scripts/install_skill.py` — copy skill to the current coding-agent host.
- `scripts/scan_intake.py` — consent-gated scan + summary JSON.
- `scripts/finalize_grade.py` — judge JSON → `GradeReport` + persistence.
- `scripts/render_grade_md.py` — deterministic Tri-pane cockpit markdown from finalized JSON.
- `scripts/render_grade_html.py` — v3 HTML twin of the same report JSON.
- `scripts/judge_schema.py` — validate and parse the host model's structured output.
- `scripts/score_math.py` — pure weighted percent/band/caps computation.
- `scripts/normalize.py` — redact + normalize any adapter output into a `PromptRecord`.
- `scripts/model_class.py` — infer `standard` / `reasoning` / `unknown` target model class.
- `scripts/store.py` / `scripts/retention.py` — local `~/.grader` store + 30-day purge.

## Judge consistency (model agnostic)

Grader splits scoring into two layers (full contract in `references/judge-consistency.md`):

| Layer | Owner | Stable across host models? |
|-------|-------|--------------------------|
| Percent, band, caps, render | Python (`score_math`, `finalize_grade`, renderers) | Yes — same judge JSON → same grade |
| Dimension levels, classification, rationales | Host LLM (you) | No — different judges may disagree |

**Hard rule:** every learner-facing grade flows from **per-prompt host-LLM judge JSON** passed to `finalize_grade.py`. Heuristic batch judges, keyword rubrics, and scripted dimension shortcuts are **forbidden** as substitutes (internal dev calibration only).

**D5** depends on `target_model_class` by design — D5 scores are not cross-class comparable. When class is `unknown`, D5 is excluded from the denominator (AS-005).

At scale (>30 prompts), sample per `flows/grade.md` scale playbook; each sampled prompt still needs full judge JSON.

## References

- `references/judge-consistency.md` — deterministic vs stochastic layers; no-heuristic rule; D5 cross-class policy; batch playbook link.
- `references/rubric-sheet.md` — full judge-facing rubric and teaching fixes.
- `references/judge-schema.json` — JSON schema for the host model's grade output.
- `prompt-quality-research-and-rubric.md` — research synthesis and rubric source.
