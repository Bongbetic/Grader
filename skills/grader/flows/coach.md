# Coach flow

Use this flow when the user asks to be coached, trained, assessed live, or helped to prompt better. Coach flow combines a historical baseline with live tasks and is the only flow that can write completed coach history.

## 1. Build a historical baseline

From this skill directory, run the shared dig when host filesystem access is available:

```bash
python scripts/extract_dossier.py --limit 100 --prompt-limit 100
```

If local dig is unavailable, ask for `/export`, pasted prompts, or an uploaded transcript and use the export path:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

Read `checklist.md` and `signals.md`. Score a concise baseline Prompt DNA from history, but keep the written summary brief: 3-5 bullets on prior DNA, strongest habits, and weakest habits.

## 2. Select the live assessment

Use the bundled coach task bank through `scripts/coach_tasks.py` and `references/coach_tasks.json`. The helper `select_live_assessment` returns four tasks: 1 easy, 2 medium, and 1 hard.

Example helper invocation from this directory:

```bash
python - <<'PY'
import sys

sys.path.insert(0, "scripts")
from coach_tasks import load_coach_tasks, select_live_assessment

tasks = select_live_assessment(load_coach_tasks())
for task in tasks:
    print(task["id"], task["complexity"], task["title"])
PY
```

Present the four tasks one-by-one. For each task:

1. Show the title, complexity, and problem.
2. Ask the user to write the prompt they would give an agent.
3. Wait for the answer before revealing the next task.
4. Grade the answer against the task's `must_cover` and `failure_modes`, plus the general checklist dimensions.

Do not batch all tasks at once unless the user explicitly asks.

## 3. Build the coach profile and report card

Create `profile.json` using `scripts/profile_schema.py` shape with:

- `meta.flow`: `coach`
- historical baseline coverage fields from the dossier
- `dna`: updated DNA that blends historical baseline and live assessment evidence
- `scores.skill`: A-D historical + live prompting craft score
- `scores.efficiency`: A-D conversation efficacy score; never token/cost/latency/cache based
- `scores.consistency`: A-D comparison of history vs live task behavior
- `habits`: focus habits for coaching
- `learning_cards`: specific concepts the user should retain
- `practice_pack`: drills targeted to the weakest habits
- `live_assessment`: task IDs, prompt answers, per-task verdicts, missing `must_cover` items, and strongest/weakest observed behaviors
- `overall_letter`: exactly one A-D letter

In markdown, include a report card section that separates:

- **History baseline:** what the prior dossier showed.
- **Live assessment:** how the four answers performed.
- **Delta:** what improved or regressed when the user knew they were being coached.

Render:

```bash
python scripts/render_report.py --in profile.json --out report.html
```

## 4. Coach the weakest habits

After the report card, run at least one coaching drill round on the weakest 1-2 habits:

- Explain the habit in plain language.
- Show a weak pattern from history or live answers.
- Give a stronger prompt pattern.
- Ask the user to revise one live answer.
- Grade the revision briefly and name the next improvement.

If the user stops before completing all four live tasks or before at least one drill round, do not record a completed coach session.

## 5. Append coach history on success

Only after all of these are true:

- The four-task live assessment is finished.
- At least one coaching drill round happened.
- The session is ready to be counted as completed.

Append through `append_coach_session` in `scripts/history_lib.py`; do not hand-edit history when the helper is available. The history file is:

```text
{claude_root}/skills/grader/history/coach_sessions.jsonl
```

Record fields should include enough data for trends:

```python
from datetime import datetime, timezone
import sys

sys.path.insert(0, "scripts")
from history_lib import append_coach_session, trends_unlock_status

record = {
    "id": "<stable-session-id>",
    "flow": "coach",
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "completed": True,
    "live_assessment_finished": True,
    "coaching_drill_rounds": 1,
    "dna_scores": {
        "clarity": 0,
        "context": 0,
        "success_criteria": 0,
        "structure": 0,
        "constraints": 0,
        "examples": 0,
        "agentic_hygiene": 0,
        "cross_session_consistency": 0,
    },
    "scores": {"skill": "B", "efficiency": "B", "consistency": "B"},
    "habits_focus": ["success_criteria", "constraints"],
    "live_assessment_task_ids": ["..."],
    "profile_path": "profile.json",
    "report_path": "report.html",
}
path = append_coach_session(record)
status = trends_unlock_status()
print(path)
print(f'{status["completed"]}/{status["required"]}')
```

Replace placeholder scores and IDs with actual values. `append_coach_session` normalizes `completed` using the completion rules.

End by telling the user the trends progress as `N/5` completed Coach sessions and where the HTML report was written.
