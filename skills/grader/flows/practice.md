# Practice flow

Use this flow when the user asks to practice prompting, wants exercises, or wants feedback on practice answers. Practice is training-only; it gives no coach history credit and no trends credit.

## 1. Pick the practice dimension

Select the weakest failing dimension from local trends if available, otherwise fall back to `D1`:

```python
import sys
sys.path.insert(0, "scripts")
from practice_session import pick_practice_dimension

dimension_id = pick_practice_dimension()
```

If the `trends` module is not present, `pick_practice_dimension` returns `D1`.

## 2. Generate one exercise

Create a single realistic, scoped exercise targeting that dimension. Include:

1. Scenario.
2. User goal.
3. Hidden grading focus, stated plainly so the user knows what to practice.
4. Optional hint only after the user attempts the exercise.

Do not reveal a perfect answer until the user asks.

## 3. Learner submits a prompt

Wait for the user to write and submit a practice prompt for the exercise.

## 4. Judge and finalize

Run the same judge + finalize path as `flows/grade.md`:

1. Read `references/rubric-sheet.md` and `references/judge-schema.json`.
2. **You are the judge** — score the practice prompt yourself and return only schema JSON.
3. Write the JSON object and pass it to `finalize_grade.py`.
4. Run `scripts/finalize_grade.py` to produce a `GradeReport`.

## 5. Coach the result

Call `teaching.coaching_notes` on the `GradeReport`:

```python
from teaching import coaching_notes

coaching = coaching_notes(report)
```

Show the user the relevant dimension, the `fix_text`, and the linked `lesson_ref`. Provide one concrete rewrite of their practice prompt.

## 6. Record the practice session

Call `practice_session.record`:

```python
from practice_session import record

record({
    "id": "<practice-session-id>",
    "prompt_id": "<practice-prompt-id>",
    "dimension_id": dimension_id,
    "learner_prompt": user_prompt,
    "grade_report": report,
    "coaching_notes": coaching,
    "exemplar": {
        "id": "<unique-id>",
        "dimension": dimension_id,
        "before": user_prompt,
        "after": rewritten_prompt,
    },
})
```

This appends the session to `~/.grader/practice.jsonl`. If the user opted in with the opt-in flag `auto_exemplar_opt_in: true` in `~/.grader/config.json` and an `exemplar` is provided, the exemplar is also saved to `curriculum/exemplars/auto/` via `curriculum.add_auto_exemplar`.

## 7. No history credit

Practice does not append coach history and does not unlock trends. If the user wants tracked progress, offer the full Coach flow or the Grade flow.
