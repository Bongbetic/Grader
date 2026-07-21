---
name: grader
description: Grades recent Claude Code user prompting quality (A–D) from local session history using a distilled best-practices checklist and light efficacy signals. Use when the user asks to grade prompts, assess prompting skill, review prompting habits, or run grader.
disable-model-invocation: false
---

# Grader

## Hard gates
- Do NOT use token counts, cost, spend, burn, cache, or latency as grading inputs or report fields.
- Produce exactly one overall letter grade: A, B, C, or D.
- Prefer Path A (auto-dig). On failure, use Path B (export/paste) into the same dossier schema.
- Grade the dossier against `checklist.md`. Use `signals.md` only as light modifiers.
- Cite evidence snippets from the sample. If no inconsistencies, write "none found".

## Procedure

### 1. Build dossier (Path A)
Run from this skill directory (adjust if installed under `~/.claude/skills/grader`):

```bash
python scripts/extract_dossier.py --limit 30
```

If exit code 2 or Claude root missing → go to Path B.

### 2. Path B fallback
Ask the user to run Claude Code `/export` for recent sessions (or paste transcripts). Save to a temp file if needed, then:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

If paste: write paste to temp file and use `--export` with intake noted as paste in the report (or `--intake paste` if implemented).

### 3. Grade
Read `checklist.md` and `signals.md`. Score applicable dimensions across the dossier (aggregate last N sessions, report coverage `sessions_graded/30`). Apply consistency + signal modifiers per those files.

### 4. Report template
Emit markdown with ALL sections:

1. Overall grade
2. Coverage (`sessions_graded/30`, intake path)
3. Evidence
4. Strengths
5. Gaps
6. Inconsistencies
7. Improve next (3–5 actions)
8. Weak → stronger (2–3 rewrites grounded in their prompts)

Do not upload transcripts. Keep redactions secrets redacted.

## Bundled rubric
See checklist.md and signals.md in this skill folder — read them before grading.
