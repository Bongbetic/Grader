---
name: grader
description: Builds a Prompting Profile from Claude Code history or pasted transcripts. Use when asked to grade prompts, review prompting habits, run grader, coach prompting, practice prompting, show progress, or show trends.
disable-model-invocation: false
---

# Grader

Works on **Claude Code** (CLI / Code Desktop) and **Claude Desktop / claude.ai** (uploaded skill with code execution). Keep the skill name `/grader`.

## Hard gates

- Do NOT use token counts, cost, spend, burn, cache, model tier, or latency as grading inputs or report fields.
- Conversation efficacy is allowed only as prompts-per-task, single-shot completion, rework rate, clarification/correction loops, and abandoned-goal evidence. Keep efficacy separate from token/cost narratives.
- Emit exactly one overall letter grade: A, B, C, or D. The letter is a side effect of the richer Prompting Profile.
- Report separated axes when grading: Skill, Efficiency, and Consistency.
- Grade against `checklist.md`. Use `signals.md` only as light modifiers under its rules.
- Cite evidence snippets from the sample for each material claim. If no inconsistencies are found, write "none found".
- Do not upload transcripts to third parties. Keep redacted secrets redacted.
- Do not append coach history except in the Coach flow after completion rules are satisfied.

## Surface detection

| Surface | How to tell | Intake |
|---------|-------------|--------|
| Claude Code (CLI or Code in Desktop) | You can run shell tools and read the host filesystem | Prefer **Path A**, then Path B |
| Claude Desktop / claude.ai chat | Code execution sandbox; host `~/.claude` usually unavailable | Prefer **Path B** (paste / upload export). Skip Path A if dig fails |

## Intent router

After determining the user's intent, read the matching `flows/*.md` file and follow it.

| Intent | User language | Flow file | Notes |
|--------|---------------|-----------|-------|
| Grade (default) | `/grader`, "grade my prompts", "run grader", "review my prompting habits", ambiguous grader request | `flows/grade.md` | Historical Prompting Profile. Do not append coach history. |
| Coach | "coach me", "train me", "coach me to prompt better", "live assessment", "help me improve prompting" | `flows/coach.md` | Historical baseline + four live tasks via `coach_tasks.py`; only completed Coach sessions count toward trends. |
| Practice | "I want to practice prompting", "give me exercises", "drill me", "grade these practice replies" | `flows/practice.md` | 5-10 targeted exercises. No history credit. |
| Trends | "show my trends", "progress", "history", "multi-week view", "am I unlocked" | `flows/trends.md` | Render trends from completed Coach history; unlock requires 5 completed Coach sessions. |

When multiple intents appear, prefer the most specific active request: Trends > Coach > Practice > Grade. If the user asks to grade first and then practice, complete Grade and offer Practice.

## Shared intake procedure

### 1. Build dossier - Path A (Claude Code / local dig)
Only when host filesystem access is available. From this skill directory:

```bash
python scripts/extract_dossier.py --limit 100 --prompt-limit 100
```

Windows tip: if console encoding errors, set `PYTHONIOENCODING=utf-8` or write `--out dossier.json`.

If exit code 2, Claude root missing, or no host FS -> go to Path B.

### 2. Build dossier - Path B (fallback / Desktop primary)
Ask the user for recent prompts via:
- Claude Code `/export`, or
- Paste chat turns (`Human:` / `User:` / `Assistant:`), or
- Upload an export file into the conversation / code-execution workspace

Then either:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

Or, if Python/scripts are unavailable: parse user turns into the same logical dossier shape (`sessions[]` with `user_prompts` + light signals) using the rules in `scripts/grader_lib.py` / this skill, then continue.

Mark `intake_path` as `export` or `paste`. Report coverage using `prompts_sampled`, `prompts_available`, `sessions_scanned`, and `sessions_graded` from the dossier.

### 3. Follow the selected flow

After the dig, read the matching flow playbook and follow it:

- `flows/grade.md`
- `flows/coach.md`
- `flows/practice.md`
- `flows/trends.md`

All grading flows must read `checklist.md` and `signals.md` before scoring.

## Render commands

Prompting Profile HTML:

```bash
python scripts/render_report.py --in profile.json --out report.html
```

Trends HTML:

```bash
python scripts/render_trends.py --root ... --out trends.html
```

Use the actual Claude root for `--root` when known. If it is omitted, scripts resolve `CLAUDE_CONFIG_DIR` or `~/.claude`.

## Coach tasks and history

- Coach tasks are selected through `scripts/coach_tasks.py` from `references/coach_tasks.json`.
- The Coach flow uses `select_live_assessment` to present four tasks one-by-one.
- History is stored at `{claude_root}/skills/grader/history/coach_sessions.jsonl`.
- Append history through `append_coach_session` in `scripts/history_lib.py` only after Coach completion.
- Trends unlock after 5 completed Coach sessions. A completion requires `completed`, `live_assessment_finished`, and at least one `coaching_drill_rounds`.

## Bundled rubric

See `checklist.md` and `signals.md` in this skill folder - read them before grading or coaching.
