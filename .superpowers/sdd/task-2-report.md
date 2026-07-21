# Task 2 Report: Task segmentation + efficiency aggregates

## Summary

Implemented task segmentation and efficiency aggregation in `skills/grader/scripts/grader_lib.py`.

Added:
- `TASK_CONTINUITY_THRESHOLD: float = 0.3`
- `segment_tasks(user_prompts: list[str]) -> list[dict[str, Any]]`
- `_task_from_prompts(prompts: list[str], indices: list[int]) -> dict[str, Any]`
- `compute_efficiency(tasks: list[dict[str, Any]]) -> dict[str, Any]`
- `attach_efficiency(dossier: dict[str, Any]) -> dict[str, Any]`

Both dossier builders now call `attach_efficiency` before returning:
- `build_dossier_from_claude_root`
- `build_dossier_from_export`

`extract_dossier.py` did not require a direct edit because it already emits the objects returned by those builders, so CLI output now includes `efficiency` through the shared library path.

## TDD Evidence

1. Added the brief-specified tests in `tests/test_grader_lib.py`.
2. Ran targeted tests before implementation:
   - Command: `python3 -m pytest tests/test_grader_lib.py::test_segment_tasks_splits_on_topic_shift_and_merges_corrections tests/test_grader_lib.py::test_compute_efficiency_math -v`
   - Result: failed at import time because `attach_efficiency` was missing.
3. Implemented segmentation, task summaries, efficiency math, and dossier attachment.
4. Added integration coverage for `attach_efficiency` and builder output.
5. Verified all tests pass.

## Test Results

Commands run:

```bash
python3 -m pytest tests/test_grader_lib.py::test_segment_tasks_splits_on_topic_shift_and_merges_corrections tests/test_grader_lib.py::test_compute_efficiency_math -v
python3 -m pytest tests/test_grader_lib.py -v
python3 -m pytest -v
```

Final result:

```text
22 passed in 0.11s
```

## Self-Review

- Confirmed threshold value and type annotation match the brief.
- Confirmed task dicts include prompt indices, full prompts, prompt count, corrections, restates, and resolved state.
- Confirmed efficiency summaries omit full prompt text while retaining counts and indices.
- Confirmed empty input returns zeroed metrics and `worst_task: None`.
- Confirmed CLI tests still pass with the additional `efficiency` field in output.

## Concerns

- Segmentation is intentionally heuristic and follows the brief exactly; adjacent prompts from different sessions are flattened by `attach_efficiency`, so overlapping prompts across session boundaries can be grouped into one task.
