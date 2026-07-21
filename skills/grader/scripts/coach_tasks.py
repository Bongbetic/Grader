from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


TASKS_PATH = Path(__file__).resolve().parents[1] / "references" / "coach_tasks.json"
ASSESSMENT_MIX = {
    "easy": 1,
    "medium": 2,
    "hard": 1,
}


def load_coach_tasks(path: str | Path | None = None) -> list[dict[str, Any]]:
    task_path = Path(path) if path is not None else TASKS_PATH
    with task_path.open(encoding="utf-8") as f:
        tasks = json.load(f)
    if not isinstance(tasks, list):
        raise ValueError(f"coach task bank must be a JSON list: {task_path}")
    return tasks


def select_live_assessment(
    tasks: list[dict[str, Any]],
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    picker = rng if rng is not None else random.Random()
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for complexity, required_count in ASSESSMENT_MIX.items():
        candidates = _unique_candidates(tasks, complexity, selected_ids)
        if len(candidates) < required_count:
            raise ValueError(
                f"not enough unique {complexity} coach tasks: "
                f"need {required_count}, found {len(candidates)}"
            )
        picked = picker.sample(candidates, required_count)
        selected.extend(picked)
        selected_ids.update(str(task["id"]) for task in picked)

    return selected


def _unique_candidates(
    tasks: list[dict[str, Any]],
    complexity: str,
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task.get("id", ""))
        if task.get("complexity") != complexity or not task_id:
            continue
        if task_id in excluded_ids or task_id in seen:
            continue
        seen.add(task_id)
        candidates.append(task)
    return candidates
