# Coach flow

Use this flow when the user asks to be coached, trained, or helped to rewrite a specific prompt. Coach is a teaching session built around a concrete graded prompt. It does not create v2 coach history credit and does not unlock trends.

## 1. Require a GradeReport in-session

Coach works on a real prompt, not abstract advice. If the user has not just completed a Grade flow, ask them to paste a prompt and run it through the same judge + finalize path as `flows/grade.md` before coaching.

Do not coach without a `GradeReport` from `scripts/finalize_grade.py`.

## 2. Load teaching notes

Call `teaching.coaching_notes` on the in-session report:

```python
import sys
sys.path.insert(0, "scripts")
from teaching import coaching_notes

notes = coaching_notes(report)
```

Each note contains `dimension_id`, `fix_text`, and `lesson_ref`. Only dimensions with level < 3 are returned.

## 3. Pick one dimension and link its lesson

Choose the lowest-scoring dimension from the notes (or the first if tied). Show the user:

1. The dimension and what it measures.
2. The `fix_text` teaching prompt.
3. The linked lesson:

```python
from curriculum import load_lesson

lesson = load_lesson(note["lesson_ref"])
```

## 4. Rewrite the prompt in learning-first voice

Write a concrete "after" version of the user's prompt that fixes the weak dimension. Explain what changed in one or two sentences. Ask the user to compare the original and the rewrite.

Keep the voice learning-first: show the stronger pattern, do not just score the mistake.

## 5. Optional revision round

If the user revises their prompt, re-run the judge + `finalize_grade.py` path and compare the new `GradeReport` to the original. Name any gains and the next improvement.

## 6. No coach history credit

Do not append to the v2 coach history file. Do not call the v2 trends unlock helper. Coach is teaching-only; it does not count toward trends unlock. If the user wants tracked progress, offer the Grade flow or the Trends flow.
