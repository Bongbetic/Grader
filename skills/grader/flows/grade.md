# Grade flow

Use this flow for the default `/grader` intent: grade the user's historical prompting craft and produce a Prompting Profile. The overall A-D grade is required, but the product identity is the profile, not the letter alone.

## 1. Build the dossier

From this skill directory, prefer the local Claude Code dig when host filesystem access is available:

```bash
python scripts/extract_dossier.py --limit 100 --prompt-limit 100
```

If the host Claude root is unavailable, ask for a Claude Code `/export`, pasted transcript, or uploaded export file, then run:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

If scripts are unavailable, construct the same logical dossier manually: `sessions[]` with `user_prompts`, `signals`, `prompts_sampled`, `prompts_available`, `sessions_scanned`, and `intake_path`.

## 2. Read the grading sources

Before scoring, read:

- `checklist.md` for dimensions, N/A rules, letter derivation, and separated score axes.
- `signals.md` for allowed conversation efficacy modifiers and forbidden metrics.

Do not use token counts, cost, spend, cache, model tier, or latency as grading inputs or report fields.

## 3. Fill the Prompting Profile JSON

Create a local `profile.json` using the shape in `scripts/profile_schema.py`.

Required content:

- `meta.flow`: `grade`
- `meta.intake_path`, `meta.prompts_sampled`, `meta.prompts_available`, `meta.sessions_scanned`
- `dna`: all checklist dimensions using the IDs from `checklist.md`
  - `score`: 0-10 when applicable, or `null` for true N/A
  - `verdict`: Strong, Adequate, Weak, or N/A with a short rationale
  - `evidence`: quoted snippets from user prompts; cite "none found" only for inconsistency evidence when appropriate
- `scores.skill`: the checklist-derived A-D letter
- `scores.efficiency`: a separate A-D conversation efficacy assessment using prompts-per-task, single-shot completion, and rework patterns only
- `scores.consistency`: a separate A-D stability assessment across sampled sessions
- `efficiency`: summarize the dossier efficiency object in user-facing terms
- `habits`: recurring prompting habits, both strengths and gaps
- `learning_cards`: 3-5 specific lessons
- `practice_pack`: 3-5 targeted exercises for the weakest dimensions
- `live_assessment`: `null`
- `overall_letter`: exactly one A, B, C, or D. It should match the Skill letter unless a local report convention explicitly separates display and skill grade.

## 4. Produce the markdown report

Lead with a Profile hero:

```markdown
# Your Prompting Profile

**Overall:** <A-D>
**Coverage:** <prompts_sampled>/<prompts_available> prompts, <sessions_scanned> sessions scanned, intake path `<path>`
```

Then include:

1. Prompt DNA table with dimension, verdict, score, and evidence.
2. Report card with separated Skill, Efficiency, and Consistency scores.
3. Strengths.
4. Gaps.
5. Inconsistencies, or "none found" when supported.
6. Learning cards.
7. Practice pack.
8. Weak to stronger rewrites grounded in the user's prompts.

Emit exactly one overall letter grade as a side effect of the profile. Keep the richer DNA and practice guidance prominent.

## 5. Render the HTML artifact

Render the profile:

```bash
python scripts/render_report.py --in profile.json --out report.html
```

Tell the user where `profile.json` and `report.html` were written. If rendering fails, still provide the markdown report and mention the render error.

## 6. Offer practice

Offer to grade a short follow-up practice loop against the weakest dimensions. If the user accepts, switch to the Practice flow.

Do not append coach history in Grade flow. History credit is only for completed Coach sessions.
