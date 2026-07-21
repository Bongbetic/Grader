---
name: grader
description: Grades prompting quality (A–D) from Claude Code history or pasted transcripts. Use when asked to grade prompts, review prompting habits, or run grader.
disable-model-invocation: false
---

# Grader

Works on **Claude Code** (CLI / Code Desktop) and **Claude Desktop / claude.ai** (uploaded skill with code execution).

## Hard gates
- Do NOT use token counts, cost, spend, burn, cache, or latency as grading inputs or report fields.
- Produce exactly one overall letter grade: A, B, C, or D.
- Grade against `checklist.md`. Use `signals.md` only as light modifiers.
- Cite evidence snippets from the sample. If no inconsistencies, write "none found".
- Do not upload transcripts to third parties. Keep redacted secrets redacted.

## Surface detection

| Surface | How to tell | Intake |
|---------|-------------|--------|
| Claude Code (CLI or Code in Desktop) | You can run shell tools and read the host filesystem | Prefer **Path A**, then Path B |
| Claude Desktop / claude.ai chat | Code execution sandbox; host `~/.claude` usually unavailable | Prefer **Path B** (paste / upload export). Skip Path A if dig fails |

## Procedure

### 1. Build dossier — Path A (Claude Code / local dig)
Only when host filesystem access is available. From this skill directory:

```bash
python scripts/extract_dossier.py --limit 30
```

Windows tip: if console encoding errors, set `PYTHONIOENCODING=utf-8` or write `--out dossier.json`.

If exit code 2, Claude root missing, or no host FS → go to Path B.

### 2. Build dossier — Path B (fallback / Desktop primary)
Ask the user for recent prompts via:
- Claude Code `/export`, or
- Paste chat turns (`Human:` / `User:` / `Assistant:`), or
- Upload an export file into the conversation / code-execution workspace

Then either:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

Or, if Python/scripts are unavailable: parse user turns into the same logical dossier shape (`sessions[]` with `user_prompts` + light signals) using the rules in `scripts/grader_lib.py` / this skill, then continue.

Mark `intake_path` as `export` or `paste`. Report coverage as `sessions_graded/30` (or `n/30` if fewer).

### 3. Grade
Read `checklist.md` and `signals.md`. Score applicable dimensions across the dossier. Apply consistency + signal modifiers per those files.

### 4. Report template
Emit markdown with ALL sections:

1. Overall grade
2. Coverage (`sessions_graded/30`, intake path, surface if known)
3. Evidence
4. Strengths
5. Gaps
6. Inconsistencies
7. Improve next (3–5 actions)
8. Weak → stronger (2–3 rewrites grounded in their prompts)

## Bundled rubric
See `checklist.md` and `signals.md` in this skill folder — read them before grading.
