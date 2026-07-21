# Grader Multi-Flow Prompt Coach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve the Claude Code `/grader` skill into a multi-flow Prompting Profile product (Grade / Coach / Practice / Trends) that absorbs v2 sampling/efficiency/HTML work while keeping the `/grader` name.

**Architecture:** Shared Python collector/analyzer/history/renderers plus intent-routed markdown playbooks under `skills/grader/flows/`. LLM performs craft judgment; Python owns sampling math, task segmentation, efficiency aggregates, Coach completion counting, and trends gating.

**Tech Stack:** Python 3.11+ (stdlib only at runtime), pytest, Claude Code skill markdown (`SKILL.md` + flow playbooks), self-contained HTML (inline CSS/SVG, no CDN).

**Spec:** `docs/superpowers/specs/2026-07-21-grader-coach-design.md`

## Global Constraints

- Keep skill folder and command name exactly `grader` / `/grader` — do not rename to coach.
- Claude Code filesystem is primary; history is local only under the Claude config dir.
- Never use token counts, cost, spend, burn, cache, or latency as scoring inputs or primary report fields.
- Efficiency means prompts-per-task conversation efficacy — never frame as resource/brevity reward.
- Sample unit is 100 prompts newest-first (`DEFAULT_PROMPT_LIMIT = 100`); `DEFAULT_SESSION_LIMIT` becomes scan ceiling `100`.
- Trends unlock only after **5** Coach sessions with `completed: true` (live assessment finished **and** ≥1 coaching/practice drill round).
- Evidence cites must use real `session#/prompt#` (or live-task ids); no fabricated evidence.
- HTML renderers must be self-contained: no external `http://` / `https://` asset URLs and no remote `src=`.
- Runtime remains stdlib-only (pytest is test-only via `requirements.txt`).
- Every task ends with tests green and a commit on the working branch.

## File structure (create / modify)

| Path | Responsibility |
|------|----------------|
| `skills/grader/scripts/grader_lib.py` | Prompt-capped pooling, task segmentation, efficiency aggregates, dossier fields |
| `skills/grader/scripts/history_lib.py` | Coach history JSONL, completion rules, trends unlock counter |
| `skills/grader/scripts/profile_schema.py` | Empty profile JSON shape + light validation helpers |
| `skills/grader/scripts/render_report.py` | Profile / report-card HTML from profile JSON |
| `skills/grader/scripts/render_trends.py` | Gated trends HTML charts from history records |
| `skills/grader/scripts/extract_dossier.py` | CLI: `--prompt-limit`, attach efficiency to dossier |
| `skills/grader/SKILL.md` | Intent router + hard gates + shared dig procedure |
| `skills/grader/flows/grade.md` | Grade playbook |
| `skills/grader/flows/coach.md` | Coach playbook |
| `skills/grader/flows/practice.md` | Practice playbook |
| `skills/grader/flows/trends.md` | Trends playbook |
| `skills/grader/checklist.md` | Per-dimension Strong/Adequate/Weak/N/A + letter rollup + DNA mapping |
| `skills/grader/signals.md` | Allow prompts-per-task efficacy; keep token/cost wall |
| `skills/grader/references/coach_tasks.json` | Live assessment task bank |
| `tests/test_grader_lib.py` | Update session-limit test; add prompt-cap / segmentation / efficiency |
| `tests/test_history_lib.py` | Completion counting + unlock gate |
| `tests/test_profile_schema.py` | Profile shape |
| `tests/test_render_report.py` | Self-contained profile HTML |
| `tests/test_render_trends.py` | Deny/allow + self-contained charts |
| `README.md` | Document multi-flow usage briefly |

**Finalized open details from the spec:**

- History file: `{claude_root}/skills/grader/history/coach_sessions.jsonl` (override root via `CLAUDE_CONFIG_DIR` / `resolve_claude_root()`).
- Live assessment mix: **1 easy + 2 medium + 1 hard** (4 tasks); no repeat of same `id` within one Coach session.
- History writes are Claude Code–local only (skip / no-op when not on host FS).

---

### Task 1: Prompt-capped pooling (absorb v2 sampling)

**Files:**
- Modify: `skills/grader/scripts/grader_lib.py`
- Modify: `skills/grader/scripts/extract_dossier.py`
- Modify: `tests/test_grader_lib.py`
- Test: `tests/test_grader_lib.py`

**Interfaces:**
- Consumes: existing `discover_session_files`, `select_recent_sessions`, `parse_session_jsonl`, `empty_dossier`
- Produces:
  - `DEFAULT_PROMPT_LIMIT: int = 100`
  - `DEFAULT_SESSION_LIMIT: int = 100` (scan ceiling; replaces 30)
  - `build_dossier_from_claude_root(claude_root: Path, session_limit: int = DEFAULT_SESSION_LIMIT, prompt_limit: int = DEFAULT_PROMPT_LIMIT) -> dict`
  - Dossier keys: `prompts_sampled: int`, `prompts_available: int`, `sessions_scanned: int`, keep `sessions_graded` as sessions included

- [ ] **Step 1: Write the failing tests**

Add/replace in `tests/test_grader_lib.py`:

```python
def test_default_prompt_limit_is_100():
    assert grader_lib.DEFAULT_PROMPT_LIMIT == 100


def test_default_session_limit_is_100():
    assert grader_lib.DEFAULT_SESSION_LIMIT == 100


def test_build_dossier_stops_at_prompt_limit(tmp_path):
    projects = tmp_path / "projects" / "demo"
    projects.mkdir(parents=True)
    # Two sessions, 3 prompts each; prompt_limit=4 → first session full + 1 from second (newest-first)
    newer = projects / "newer.jsonl"
    older = projects / "older.jsonl"
    def write_session(path, sid, prompts, mtime_offset):
        lines = []
        for i, p in enumerate(prompts):
            lines.append(json.dumps({
                "type": "user",
                "sessionId": sid,
                "message": {"role": "user", "content": p},
                "timestamp": f"2026-07-0{i+1}T00:00:00Z",
            }))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        import os, time
        os.utime(path, (time.time() - mtime_offset, time.time() - mtime_offset))
    write_session(newer, "new", ["n1", "n2", "n3"], 0)
    write_session(older, "old", ["o1", "o2", "o3"], 100)
    d = build_dossier_from_claude_root(tmp_path, session_limit=10, prompt_limit=4)
    assert d["prompts_sampled"] == 4
    assert d["prompts_available"] == 6
    assert d["sessions_scanned"] == 2
    assert sum(s["prompt_count"] for s in d["sessions"]) == 4
    assert d["sessions"][0]["session_id"] == "new"
    assert d["sessions"][0]["user_prompts"] == ["n1", "n2", "n3"]
    assert d["sessions"][1]["user_prompts"] == ["o1"]
```

Update `test_empty_dossier_schema` expectations only if `empty_dossier` gains new keys (prefer adding keys in `build_*`, not necessarily in empty).

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_grader_lib.py::test_default_prompt_limit_is_100 tests/test_grader_lib.py::test_default_session_limit_is_100 tests/test_grader_lib.py::test_build_dossier_stops_at_prompt_limit -v`

Expected: FAIL (missing `DEFAULT_PROMPT_LIMIT` and/or old session limit 30 / no prompt capping).

- [ ] **Step 3: Implement minimal pooling**

In `grader_lib.py`:

```python
DEFAULT_SESSION_LIMIT = 100
DEFAULT_PROMPT_LIMIT = 100


def build_dossier_from_claude_root(
    claude_root: Path,
    session_limit: int = DEFAULT_SESSION_LIMIT,
    prompt_limit: int = DEFAULT_PROMPT_LIMIT,
) -> dict[str, Any]:
    found = discover_session_files(claude_root)
    selected = select_recent_sessions(found, limit=session_limit)
    dossier = empty_dossier("auto")
    dossier["sessions_found"] = len(found)
    notes: list[str] = []
    sessions: list[dict[str, Any]] = []
    prompts_sampled = 0
    prompts_available = 0
    for path in selected:
        session = parse_session_jsonl(path)
        prompts_available += session["prompt_count"]
        if session["prompt_count"] == 0:
            continue
        if prompts_sampled >= prompt_limit:
            continue
        remaining = prompt_limit - prompts_sampled
        full_prompts = session["user_prompts"]
        if len(full_prompts) > remaining:
            session = dict(session)
            session["user_prompts"] = full_prompts[:remaining]
            session["prompt_count"] = len(session["user_prompts"])
            session["partial"] = True
            session["signals"] = compute_signals(session["user_prompts"])
        for n in session.pop("_redaction_notes", []):
            if n not in notes:
                notes.append(n)
        prompts_sampled += session["prompt_count"]
        sessions.append(session)
    dossier["sessions"] = sessions
    dossier["sessions_graded"] = len(sessions)
    dossier["sessions_scanned"] = len(selected)
    dossier["prompts_sampled"] = prompts_sampled
    dossier["prompts_available"] = prompts_available
    dossier["redaction_notes"] = notes
    return dossier
```

Also set `prompts_sampled` / `prompts_available` on export dossiers (sum of included prompts).

Update `extract_dossier.py` to accept `--prompt-limit` defaulting to `DEFAULT_PROMPT_LIMIT` and pass it through.

Replace old test `test_default_session_limit_is_30` with `test_default_session_limit_is_100`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_grader_lib.py -v`

Expected: PASS (all existing + new).

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/grader_lib.py skills/grader/scripts/extract_dossier.py tests/test_grader_lib.py
git commit -m "feat: cap dossier sample at 100 prompts newest-first"
```

---

### Task 2: Task segmentation + efficiency aggregates

**Files:**
- Modify: `skills/grader/scripts/grader_lib.py`
- Modify: `skills/grader/scripts/extract_dossier.py`
- Modify: `tests/test_grader_lib.py`

**Interfaces:**
- Consumes: `_tokens`, `_jaccard`, `_CORRECTION_RE`, existing signals helpers
- Produces:
  - `TASK_CONTINUITY_THRESHOLD: float = 0.3`
  - `segment_tasks(user_prompts: list[str]) -> list[dict]`
  - `compute_efficiency(tasks: list[dict]) -> dict`
  - `attach_efficiency(dossier: dict) -> dict` (mutates/returns dossier with `efficiency` key)

Task dict shape:

```python
{
  "prompt_indices": list[int],  # indices into the flat prompt list used
  "prompts": list[str],
  "prompt_count": int,
  "corrections": int,
  "restates": int,
  "resolved": bool,  # True unless last prompt matches abandon heuristics
}
```

Efficiency shape:

```python
{
  "prompts_per_task_mean": float,
  "prompts_per_task_median": float,
  "single_shot_rate": float,  # tasks with prompt_count == 1
  "rework_rate": float,       # tasks with corrections+restates >= 1
  "tasks": list[dict],        # per-task summaries without full prompt text optional; keep counts
  "worst_task": dict | None,  # highest prompt_count task summary
}
```

- [ ] **Step 1: Write the failing tests**

```python
from grader_lib import segment_tasks, compute_efficiency, attach_efficiency


def test_segment_tasks_splits_on_topic_shift_and_merges_corrections():
    prompts = [
        "Add dark mode to settings using CSS variables",
        "No, wrong — put the toggle in the navbar instead",  # continuation (correction)
        "Write a haiku about rain",  # topic shift
    ]
    tasks = segment_tasks(prompts)
    assert len(tasks) == 2
    assert tasks[0]["prompt_count"] == 2
    assert tasks[0]["corrections"] >= 1
    assert tasks[1]["prompt_count"] == 1


def test_compute_efficiency_math():
    tasks = segment_tasks([
        "Ship login with magic link and tests",
        "Also add rate limiting to login",  # likely same task if overlap enough; if not, adjust fixture
        "Translate 'hello' to French",
    ])
    # Use explicit constructed tasks for stable math:
    tasks = [
        {"prompt_count": 1, "corrections": 0, "restates": 0, "resolved": True, "prompts": ["a"], "prompt_indices": [0]},
        {"prompt_count": 3, "corrections": 1, "restates": 0, "resolved": True, "prompts": ["b","c","d"], "prompt_indices": [1,2,3]},
    ]
    eff = compute_efficiency(tasks)
    assert abs(eff["prompts_per_task_mean"] - 2.0) < 1e-9
    assert eff["prompts_per_task_median"] == 2.0
    assert abs(eff["single_shot_rate"] - 0.5) < 1e-9
    assert abs(eff["rework_rate"] - 0.5) < 1e-9
    assert eff["worst_task"]["prompt_count"] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_grader_lib.py::test_segment_tasks_splits_on_topic_shift_and_merges_corrections tests/test_grader_lib.py::test_compute_efficiency_math -v`

Expected: FAIL (import / missing functions).

- [ ] **Step 3: Implement segmentation + efficiency**

```python
TASK_CONTINUITY_THRESHOLD = 0.3


def segment_tasks(user_prompts: list[str]) -> list[dict[str, Any]]:
    if not user_prompts:
        return []
    tasks: list[dict[str, Any]] = []
    start = 0
    for i in range(1, len(user_prompts)):
        prev, cur = user_prompts[i - 1], user_prompts[i]
        overlap = _jaccard(_tokens(prev), _tokens(cur))
        is_correction = bool(_CORRECTION_RE.search(cur))
        is_restate = overlap >= 0.8
        continuous = overlap >= TASK_CONTINUITY_THRESHOLD or is_correction or is_restate
        if not continuous:
            chunk = user_prompts[start:i]
            tasks.append(_task_from_prompts(chunk, list(range(start, i))))
            start = i
    chunk = user_prompts[start:]
    tasks.append(_task_from_prompts(chunk, list(range(start, len(user_prompts)))))
    return tasks


def _task_from_prompts(prompts: list[str], indices: list[int]) -> dict[str, Any]:
    signals = compute_signals(prompts)
    resolved = not (
        bool(prompts and _ABORT_RE.search(prompts[-1]))
        or (len(prompts) >= 3 and len(prompts[-1].strip()) < 12)
    )
    return {
        "prompt_indices": indices,
        "prompts": prompts,
        "prompt_count": len(prompts),
        "corrections": signals["corrections"],
        "restates": signals["restates"],
        "resolved": resolved,
    }


def compute_efficiency(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if not tasks:
        return {
            "prompts_per_task_mean": 0.0,
            "prompts_per_task_median": 0.0,
            "single_shot_rate": 0.0,
            "rework_rate": 0.0,
            "tasks": [],
            "worst_task": None,
        }
    counts = [t["prompt_count"] for t in tasks]
    mean = sum(counts) / len(counts)
    sorted_counts = sorted(counts)
    mid = len(sorted_counts) // 2
    median = (
        sorted_counts[mid]
        if len(sorted_counts) % 2 == 1
        else (sorted_counts[mid - 1] + sorted_counts[mid]) / 2
    )
    single = sum(1 for c in counts if c == 1) / len(counts)
    rework = sum(1 for t in tasks if (t["corrections"] + t["restates"]) >= 1) / len(counts)
    summaries = [
        {
            "prompt_count": t["prompt_count"],
            "corrections": t["corrections"],
            "restates": t["restates"],
            "resolved": t["resolved"],
            "prompt_indices": t["prompt_indices"],
        }
        for t in tasks
    ]
    worst = max(summaries, key=lambda s: s["prompt_count"])
    return {
        "prompts_per_task_mean": mean,
        "prompts_per_task_median": float(median),
        "single_shot_rate": single,
        "rework_rate": rework,
        "tasks": summaries,
        "worst_task": worst,
    }


def attach_efficiency(dossier: dict[str, Any]) -> dict[str, Any]:
    flat: list[str] = []
    for session in dossier.get("sessions", []):
        flat.extend(session.get("user_prompts") or [])
    dossier["efficiency"] = compute_efficiency(segment_tasks(flat))
    return dossier
```

Call `attach_efficiency` at end of `build_dossier_from_claude_root` and `build_dossier_from_export`.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_grader_lib.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/grader_lib.py skills/grader/scripts/extract_dossier.py tests/test_grader_lib.py
git commit -m "feat: add task segmentation and prompts-per-task efficiency"
```

---

### Task 3: History library + trends unlock gate

**Files:**
- Create: `skills/grader/scripts/history_lib.py`
- Create: `tests/test_history_lib.py`

**Interfaces:**
- Consumes: `resolve_claude_root` from `grader_lib`
- Produces:
  - `TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS = 5`
  - `history_dir(claude_root: Path | None = None) -> Path`
  - `history_path(claude_root: Path | None = None) -> Path`
  - `append_coach_session(record: dict, claude_root: Path | None = None) -> Path`
  - `load_coach_sessions(claude_root: Path | None = None) -> list[dict]`
  - `count_completed_coach_sessions(sessions: list[dict]) -> int`
  - `trends_unlock_status(claude_root: Path | None = None) -> dict`  
    → `{unlocked: bool, completed: int, required: int, remaining: int}`
  - `is_coach_completion(record: dict) -> bool` — requires `completed is True` AND `live_assessment_finished is True` AND `coaching_drill_rounds >= 1`

Record minimum fields when appending:

```python
{
  "id": str,
  "completed_at": str,  # ISO-8601
  "completed": bool,
  "live_assessment_finished": bool,
  "coaching_drill_rounds": int,
  "dna_scores": dict[str, float],  # dimension -> 0..10
  "scores": {"skill": str, "efficiency": str, "consistency": str},
  "habits_focus": list[str],
  "live_assessment_summary": dict,
  "notes": str,
}
```

- [ ] **Step 1: Write failing tests** in `tests/test_history_lib.py`

```python
from history_lib import (
    TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS,
    append_coach_session,
    count_completed_coach_sessions,
    is_coach_completion,
    load_coach_sessions,
    trends_unlock_status,
)


def test_incomplete_coach_does_not_count(tmp_path):
    root = tmp_path
    append_coach_session({
        "id": "1",
        "completed_at": "2026-07-01T00:00:00Z",
        "completed": False,
        "live_assessment_finished": False,
        "coaching_drill_rounds": 0,
        "dna_scores": {},
        "scores": {"skill": "B", "efficiency": "C", "consistency": "B"},
        "habits_focus": [],
        "live_assessment_summary": {},
        "notes": "",
    }, claude_root=root)
    assert count_completed_coach_sessions(load_coach_sessions(root)) == 0
    status = trends_unlock_status(root)
    assert status["unlocked"] is False
    assert status["completed"] == 0
    assert status["required"] == 5
    assert status["remaining"] == 5


def test_trends_unlocks_at_five_completed(tmp_path):
    assert TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS == 5
    root = tmp_path
    for i in range(4):
        append_coach_session({
            "id": str(i),
            "completed_at": f"2026-07-0{i+1}T00:00:00Z",
            "completed": True,
            "live_assessment_finished": True,
            "coaching_drill_rounds": 1,
            "dna_scores": {"clarity": 5},
            "scores": {"skill": "B", "efficiency": "B", "consistency": "B"},
            "habits_focus": ["constraints"],
            "live_assessment_summary": {"tasks": 4},
            "notes": "",
        }, claude_root=root)
    assert trends_unlock_status(root)["unlocked"] is False
    assert trends_unlock_status(root)["remaining"] == 1
    append_coach_session({
        "id": "5",
        "completed_at": "2026-07-05T00:00:00Z",
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 2,
        "dna_scores": {"clarity": 7},
        "scores": {"skill": "A", "efficiency": "B", "consistency": "A"},
        "habits_focus": ["constraints"],
        "live_assessment_summary": {"tasks": 4},
        "notes": "improved",
    }, claude_root=root)
    status = trends_unlock_status(root)
    assert status["unlocked"] is True
    assert status["completed"] == 5
    assert status["remaining"] == 0


def test_is_coach_completion_requires_drill_round():
    assert is_coach_completion({
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 1,
    })
    assert not is_coach_completion({
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 0,
    })
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_history_lib.py -v`

- [ ] **Step 3: Implement `history_lib.py`**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from grader_lib import resolve_claude_root

TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS = 5


def history_dir(claude_root: Path | None = None) -> Path:
    root = claude_root if claude_root is not None else resolve_claude_root()
    return root / "skills" / "grader" / "history"


def history_path(claude_root: Path | None = None) -> Path:
    return history_dir(claude_root) / "coach_sessions.jsonl"


def is_coach_completion(record: dict[str, Any]) -> bool:
    return bool(
        record.get("completed")
        and record.get("live_assessment_finished")
        and int(record.get("coaching_drill_rounds") or 0) >= 1
    )


def append_coach_session(record: dict[str, Any], claude_root: Path | None = None) -> Path:
    path = history_path(claude_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Force completed flag to match rule so callers cannot mark completed incorrectly
    normalized = dict(record)
    normalized["completed"] = is_coach_completion(normalized)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return path


def load_coach_sessions(claude_root: Path | None = None) -> list[dict[str, Any]]:
    path = history_path(claude_root)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def count_completed_coach_sessions(sessions: list[dict[str, Any]]) -> int:
    return sum(1 for s in sessions if is_coach_completion(s))


def trends_unlock_status(claude_root: Path | None = None) -> dict[str, Any]:
    completed = count_completed_coach_sessions(load_coach_sessions(claude_root))
    required = TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS
    remaining = max(0, required - completed)
    return {
        "unlocked": completed >= required,
        "completed": completed,
        "required": required,
        "remaining": remaining,
    }
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_history_lib.py tests/test_grader_lib.py -v`

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/history_lib.py tests/test_history_lib.py
git commit -m "feat: add coach history store and trends unlock gate"
```

---

### Task 4: Profile JSON schema helpers

**Files:**
- Create: `skills/grader/scripts/profile_schema.py`
- Create: `tests/test_profile_schema.py`

**Interfaces:**
- Produces:
  - `DNA_DIMENSIONS: list[str]` — the 8 checklist dimension ids
  - `empty_profile(flow: str, meta: dict | None = None) -> dict`
  - `validate_profile_keys(profile: dict) -> list[str]` — returns list of missing top-level keys (empty if ok)

Profile top-level keys (exact):  
`meta`, `dna`, `scores`, `efficiency`, `habits`, `learning_cards`, `practice_pack`, `live_assessment`, `overall_letter`

- [ ] **Step 1: Failing tests**

```python
from profile_schema import DNA_DIMENSIONS, empty_profile, validate_profile_keys


def test_empty_profile_has_required_keys_and_eight_dna_slots():
    p = empty_profile("grade", meta={"intake_path": "auto", "prompts_sampled": 0})
    assert validate_profile_keys(p) == []
    assert p["meta"]["flow"] == "grade"
    assert len(DNA_DIMENSIONS) == 8
    assert len(p["dna"]) == 8
    assert p["scores"] == {"skill": None, "efficiency": None, "consistency": None}
    assert p["overall_letter"] is None
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement**

```python
DNA_DIMENSIONS = [
    "clarity",
    "context",
    "success_criteria",
    "structure",
    "constraints",
    "examples",
    "agentic_hygiene",
    "cross_session_consistency",
]

REQUIRED_KEYS = [
    "meta", "dna", "scores", "efficiency", "habits",
    "learning_cards", "practice_pack", "live_assessment", "overall_letter",
]


def empty_profile(flow: str, meta: dict | None = None) -> dict:
    base_meta = {"flow": flow, "intake_path": None, "prompts_sampled": 0, "prompts_available": 0, "sessions_scanned": 0}
    if meta:
        base_meta.update(meta)
        base_meta["flow"] = flow
    return {
        "meta": base_meta,
        "dna": [
            {"id": d, "label": d, "score": None, "verdict": None, "evidence": []}
            for d in DNA_DIMENSIONS
        ],
        "scores": {"skill": None, "efficiency": None, "consistency": None},
        "efficiency": {},
        "habits": [],
        "learning_cards": [],
        "practice_pack": [],
        "live_assessment": None,
        "overall_letter": None,
    }


def validate_profile_keys(profile: dict) -> list[str]:
    return [k for k in REQUIRED_KEYS if k not in profile]
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/profile_schema.py tests/test_profile_schema.py
git commit -m "feat: add shared prompting profile JSON schema helpers"
```

---

### Task 5: `render_report.py` (profile / report card HTML)

**Files:**
- Create: `skills/grader/scripts/render_report.py`
- Create: `tests/test_render_report.py`
- Create: `skills/grader/fixtures/profiles/sample_grade_profile.json` (small fixture)

**Interfaces:**
- Produces:
  - `render_profile_html(profile: dict) -> str`
  - CLI: `python render_report.py --in profile.json --out report.html`

HTML requirements:
- Includes DNA bars, Skill/Efficiency/Consistency, habits, learning cards section if present
- Title/hero uses “Your Prompting Profile”; letter secondary
- No `http://` or `https://` in attributes; no external `src=`
- Inline `<style>` + inline SVG ok

- [ ] **Step 1: Write fixture + failing test**

`sample_grade_profile.json` minimal valid profile with 2 weak DNA dims, scores Skill=B Efficiency=C Consistency=B, one habit, one learning card, overall_letter=B.

```python
import re
from pathlib import Path
from render_report import render_profile_html

FIXTURE = Path(__file__).resolve().parents[1] / "skills/grader/fixtures/profiles/sample_grade_profile.json"


def test_render_profile_html_is_self_contained_and_shows_dna():
    import json
    profile = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = render_profile_html(profile)
    assert "Your Prompting Profile" in html
    assert "Prompt DNA" in html or "DNA" in html
    assert "Skill" in html and "Efficiency" in html
    assert not re.search(r"""\ssrc\s*=\s*['\"]https?://""", html, re.I)
    assert "https://" not in html and "http://" not in html
    assert "<style" in html
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement renderer**

Implement `render_profile_html` with deterministic inline CSS (light theme, dark via `prefers-color-scheme`). DNA bar = SVG rect width from score 0–10 (treat None as 0). Escape all user-derived strings with `html.escape`.

CLI `main()` reads JSON path, writes HTML path, exit 0.

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/test_render_report.py -v`

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/render_report.py skills/grader/fixtures/profiles/sample_grade_profile.json tests/test_render_report.py
git commit -m "feat: render self-contained prompting profile HTML"
```

---

### Task 6: `render_trends.py` (gated colorful charts)

**Files:**
- Create: `skills/grader/scripts/render_trends.py`
- Create: `tests/test_render_trends.py`

**Interfaces:**
- Consumes: `trends_unlock_status`, `load_coach_sessions`, `TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS`
- Produces:
  - `build_trends_payload(claude_root: Path | None = None) -> dict`  
    `{status: trends_unlock_status..., sessions: list}` filtered to completions only when unlocked
  - `render_trends_html(payload: dict) -> str`  
    If not unlocked: HTML denial page with `N/5` and completion rules — **no charts**.  
    If unlocked: colorful inline-SVG line/bar charts for DNA clarity (or mean DNA), efficiency letter mapped, habit focus frequency.
  - CLI: `python render_trends.py --root ... --out trends.html` (exit 0 even when locked; still writes denial HTML)

- [ ] **Step 1: Failing tests**

```python
import re
from render_trends import build_trends_payload, render_trends_html
from history_lib import append_coach_session


def _complete(i, root):
    append_coach_session({
        "id": str(i),
        "completed_at": f"2026-07-{i:02d}T00:00:00Z",
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 1,
        "dna_scores": {"clarity": 3 + i, "constraints": 2 + i},
        "scores": {"skill": "B", "efficiency": "C", "consistency": "B"},
        "habits_focus": ["constraints"],
        "live_assessment_summary": {},
        "notes": "",
    }, claude_root=root)


def test_trends_html_denies_under_five(tmp_path):
    for i in range(1, 5):
        _complete(i, tmp_path)
    payload = build_trends_payload(tmp_path)
    html = render_trends_html(payload)
    assert payload["status"]["unlocked"] is False
    assert "4/5" in html or "4 of 5" in html
    assert "<polyline" not in html.lower() and "<path" not in html.lower()
    assert "complete" in html.lower()  # explains how to finish coach sessions
    assert not re.search(r"""\ssrc\s*=\s*['\"]https?://""", html, re.I)
    assert "https://" not in html


def test_trends_html_charts_when_unlocked(tmp_path):
    for i in range(1, 6):
        _complete(i, tmp_path)
    html = render_trends_html(build_trends_payload(tmp_path))
    assert "<svg" in html.lower()
    assert "https://" not in html
    assert "Prompt" in html or "Trend" in html
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement** denial + unlocked SVG charts (inline colors, no CDN fonts).

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/test_render_trends.py tests/test_history_lib.py -v`

- [ ] **Step 5: Commit**

```bash
git add skills/grader/scripts/render_trends.py tests/test_render_trends.py
git commit -m "feat: add gated multi-week trends HTML renderer"
```

---

### Task 7: Rubric + signals doc updates

**Files:**
- Modify: `skills/grader/checklist.md`
- Modify: `skills/grader/signals.md`

**Interfaces:**
- Consumes: existing 8 dimensions
- Produces: documented Strong/Adequate/Weak/N/A scale; letter derivation rule; DNA id mapping; separated Skill/Efficiency/Consistency meaning; signals allowlist for prompts-per-task efficacy

- [ ] **Step 1: Update `checklist.md`**

Add sections:

1. **Per-dimension verdicts:** Strong / Adequate / Weak / N/A with one-line criteria each (reuse existing Strong/Weak bullets; insert Adequate as partial/uneven).
2. **Letter derivation rule (words):**  
   - Map applicable non-N/A verdicts → provisional letter (mostly Strong→A/B band, mixed→B/C, mostly Weak→C/D).  
   - Consistency gaps can lower one step.  
   - Signal modifiers at most one additional step per existing rules.  
   - Separated Efficiency score does **not** change Skill letter directly; report both.
3. **DNA mapping table:** dimension display name → `dna.id` from `profile_schema.DNA_DIMENSIONS`.

- [ ] **Step 2: Update `signals.md`**

Replace forbidden bullet that bans all “efficiency” framing with:

- Forbidden: token/cost/latency/cache; model-tier “efficiency”; metrics that reward brevity without craft evidence.
- **Allowed:** prompts-per-task / single-shot / rework rates as **conversation efficacy**, reported under Efficiency score — never as proof of good craft alone.

Clarify: signals remain light modifiers to Skill letter; Efficiency is a separate axis.

- [ ] **Step 3: Sanity check** — no pytest for prose; manually confirm hard gates still forbid cost/tokens.

- [ ] **Step 4: Commit**

```bash
git add skills/grader/checklist.md skills/grader/signals.md
git commit -m "docs: add DNA verdicts, letter rollup, and efficacy allow rules"
```

---

### Task 8: Coach task bank

**Files:**
- Create: `skills/grader/references/coach_tasks.json`
- Create: `skills/grader/scripts/coach_tasks.py`
- Create: `tests/test_coach_tasks.py`

**Interfaces:**
- Produces:
  - JSON list of tasks: `{id, complexity: "easy"|"medium"|"hard", title, problem, must_cover: list[str], failure_modes: list[str]}`
  - At least 3 easy, 4 medium, 3 hard (bank larger than one session)
  - `select_live_assessment(tasks: list[dict], rng=None) -> list[dict]` returns **1 easy + 2 medium + 1 hard**, unique ids

- [ ] **Step 1: Failing test**

```python
import json
from pathlib import Path
from coach_tasks import select_live_assessment, load_coach_tasks

def test_select_live_assessment_mix():
    tasks = load_coach_tasks()
    picked = select_live_assessment(tasks)
    assert [t["complexity"] for t in picked].count("easy") == 1
    assert [t["complexity"] for t in picked].count("medium") == 2
    assert [t["complexity"] for t in picked].count("hard") == 1
    assert len({t["id"] for t in picked}) == 4
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Author `coach_tasks.json`** with concrete agent-style problems (coding + non-coding). Implement loader + selector (use `random.Random` injectable for tests).

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add skills/grader/references/coach_tasks.json skills/grader/scripts/coach_tasks.py tests/test_coach_tasks.py
git commit -m "feat: add coach live-assessment task bank and selector"
```

---

### Task 9: Flow playbooks + SKILL.md intent router

**Files:**
- Create: `skills/grader/flows/grade.md`
- Create: `skills/grader/flows/coach.md`
- Create: `skills/grader/flows/practice.md`
- Create: `skills/grader/flows/trends.md`
- Modify: `skills/grader/SKILL.md`
- Modify: `README.md` (short multi-flow section)

**Interfaces:**
- Consumes: dossier CLI, render scripts, history_lib completion rules, coach task bank, checklist/signals
- Produces: LLM-facing procedures for each flow; router table in SKILL.md

- [ ] **Step 1: Write `flows/grade.md`** covering: dig with prompt limit 100 → read checklist/signals → fill profile JSON (DNA, separated scores, habits, learning cards, practice pack) → markdown report (Profile hero) → `render_report.py` → offer practice grading loop. Explicitly: do not append coach history.

- [ ] **Step 2: Write `flows/coach.md`** covering: dig baseline → summarize prior DNA briefly → `select_live_assessment` / present 4 tasks one-by-one → user answers with prompts → report card (history vs live) via profile + `render_report.py` → coach weakest habits with drills → on success call `append_coach_session` with completion fields → mention trends progress `N/5`.

- [ ] **Step 3: Write `flows/practice.md`**: dig → target weakest dims → 5–10 exercises → optional grade-replies. No history credit.

- [ ] **Step 4: Write `flows/trends.md`**: run `render_trends.py`; if locked, tell user `completed/required` and completion definition; if unlocked, show HTML path.

- [ ] **Step 5: Rewrite `SKILL.md`**

Must include:
- description still triggers on grade/coach/practice/trends language
- Hard gates (cost/tokens forbidden; efficacy allowed; one overall letter still emitted as side effect; evidence cites)
- Surface detection table (keep)
- Intent router table (Grade default / Coach / Practice / Trends)
- Shared dig commands:

```bash
python scripts/extract_dossier.py --limit 100 --prompt-limit 100
```

- “After dig, read the matching `flows/*.md` and follow it”
- HTML render commands for report + trends
- History path note

- [ ] **Step 6: Update README** with four example invocations.

- [ ] **Step 7: Commit**

```bash
git add skills/grader/SKILL.md skills/grader/flows README.md
git commit -m "feat: add multi-flow grader playbooks and intent router"
```

---

### Task 10: Packaging verification + full test suite

**Files:**
- Modify if needed: `skills/grader/scripts/package_for_desktop.py` (likely no code change — already globs)
- Create: `tests/test_package_includes_coach_assets.py` (optional but preferred)

- [ ] **Step 1: Test zip contains new assets**

```python
from pathlib import Path
import zipfile
from package_for_desktop import package

def test_package_includes_flows_and_renderers(tmp_path):
    skill = Path(__file__).resolve().parents[1] / "skills" / "grader"
    out = tmp_path / "grader.zip"
    package(skill, out)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert "grader/flows/grade.md" in names
    assert "grader/scripts/render_report.py" in names
    assert "grader/scripts/render_trends.py" in names
    assert "grader/scripts/history_lib.py" in names
    assert "grader/references/coach_tasks.json" in names
```

- [ ] **Step 2: Run full suite**

Run: `pip install -r requirements.txt && python -m pytest -v`

Expected: PASS all.

- [ ] **Step 3: Manual smoke (agent)**

1. Build sample profile HTML from fixture.  
2. Build trends denial with 4 fake completions in tmp root; unlocked with 5.  
3. Confirm `package_for_desktop.py` zip path prints OK.

- [ ] **Step 4: Commit**

```bash
git add tests/test_package_includes_coach_assets.py
git commit -m "test: verify desktop zip includes coach flow assets"
```

- [ ] **Step 5: Final commit if README/spec status tweaks remain**

Update design spec status line to “Approved; implementation plan written” if touching it:

`docs/superpowers/specs/2026-07-21-grader-coach-design.md`

```bash
git add docs/superpowers/specs/2026-07-21-grader-coach-design.md
git commit -m "docs: mark coach design approved for implementation"
```

---

## Spec coverage self-check

| Spec requirement | Task(s) |
|------------------|---------|
| 100-prompt pooling | Task 1 |
| Task segmentation + efficiency | Task 2 |
| Separated Skill/Efficiency/Consistency | Tasks 4, 5, 7, 9 |
| Prompt DNA | Tasks 4, 5, 7, 9 |
| Habits + learning cards + practice pack | Tasks 4, 5, 9 |
| Coach hybrid live assessment | Tasks 8, 9 |
| Report card HTML | Task 5, 9 |
| History + 5-session trends gate | Tasks 3, 6, 9 |
| Trends colorful HTML / deny | Task 6 |
| Practice flow no history credit | Task 9 |
| Hard gates / efficacy allow | Task 7, 9 |
| Packaging | Task 10 |
| Non-goals excluded | No tasks for confidence/archetypes/multi-model |

## Placeholder / consistency scan

- Function names aligned: `attach_efficiency`, `trends_unlock_status`, `render_profile_html`, `select_live_assessment`.
- History path consistent: `{root}/skills/grader/history/coach_sessions.jsonl`.
- Unlock constant `5` shared via `TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS`.
- No TBD steps left in tasks.
