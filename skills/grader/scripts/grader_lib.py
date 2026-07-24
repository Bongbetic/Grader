from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

DEFAULT_SESSION_LIMIT = 100
DEFAULT_PROMPT_LIMIT = 100
TASK_CONTINUITY_THRESHOLD: float = 0.3
MAX_PROMPT_CHARS = 4000
_TRUNCATED_SUFFIX = " …[truncated]"

from redact import redact_text


def redact_secrets(text: str) -> tuple[str, list[str]]:
    return redact_text(text)


def truncate_prompt(text: str) -> tuple[str, list[str]]:
    if len(text) <= MAX_PROMPT_CHARS:
        return text, []
    return text[:MAX_PROMPT_CHARS] + _TRUNCATED_SUFFIX, ["truncated_prompt"]


def empty_dossier(intake_path: str) -> dict[str, Any]:
    if intake_path not in {"auto", "export", "paste"}:
        raise ValueError(f"invalid intake_path: {intake_path}")
    return {
        "sessions_found": 0,
        "sessions_graded": 0,
        "intake_path": intake_path,
        "redaction_notes": [],
        "sessions": [],
    }


def resolve_claude_root(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = env if env is not None else os.environ
    if env.get("CLAUDE_CONFIG_DIR"):
        return Path(env["CLAUDE_CONFIG_DIR"]).expanduser()
    home = home if home is not None else Path.home()
    return home / ".claude"


def discover_session_files(claude_root: Path) -> list[Path]:
    projects = claude_root / "projects"
    if not projects.is_dir():
        return []
    return sorted(projects.rglob("*.jsonl"))


def select_recent_sessions(
    paths: list[Path], limit: int = DEFAULT_SESSION_LIMIT
) -> list[Path]:
    ranked = sorted(
        paths,
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    return ranked[:limit]


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
    return attach_efficiency(dossier)


def _parse_turns(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?im)^(human|user|assistant|claude):\s*", text))
    turns: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        role = m.group(1).lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if role in {"human", "user"}:
            turns.append(("user", body))
        else:
            turns.append(("assistant", body))
    return turns


_EXPORT_SESSION_RE = re.compile(r"(?im)^##\s+session\b[^\n]*$")
_EXPORT_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)?\b"
)


def _split_export_sessions(text: str) -> list[tuple[str | None, str]]:
    matches = list(_EXPORT_SESSION_RE.finditer(text))
    if not matches:
        return [(None, text)]

    chunks: list[tuple[str | None, str]] = []
    prelude = text[: matches[0].start()].strip()
    if prelude:
        chunks.append((None, prelude))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            chunks.append((match.group(0), body))
    return chunks or [(None, text)]


def _export_order_timestamp(header: str | None, body: str) -> str | None:
    haystack = "\n".join(part for part in [header, body[:1000]] if part)
    match = _EXPORT_TIMESTAMP_RE.search(haystack)
    return match.group(0).replace(" ", "T") if match else None


def build_dossier_from_export(
    text: str,
    intake_path: str = "export",
    prompt_limit: int = DEFAULT_PROMPT_LIMIT,
) -> dict[str, Any]:
    dossier = empty_dossier(intake_path)
    notes: list[str] = []
    available_sessions: list[dict[str, Any]] = []
    ordered_chunks = _split_export_sessions(text)
    for i, (header, chunk) in enumerate(ordered_chunks):
        turns = _parse_turns(chunk)
        prompts: list[str] = []
        assistant_qs = 0
        for role, body in turns:
            if role == "assistant" and "?" in body:
                assistant_qs += 1
            if role == "user" and body.strip():
                cleaned, n = redact_secrets(body)
                cleaned, tnotes = truncate_prompt(cleaned)
                for label in n + tnotes:
                    if label not in notes:
                        notes.append(label)
                if prompts and prompts[-1] == cleaned:
                    continue
                prompts.append(cleaned)
        if not prompts:
            continue
        started_at = _export_order_timestamp(header, chunk)
        available_sessions.append({
            "session_id": f"export-{i+1}",
            "project_path": "export",
            "started_at": started_at,
            "ended_at": started_at,
            "user_prompts": prompts,
            "prompt_count": len(prompts),
            "signals": compute_signals(prompts, assistant_qs),
        })

    if available_sessions and all(s.get("started_at") for s in available_sessions):
        available_sessions = sorted(
            available_sessions,
            key=lambda s: (str(s["started_at"]), str(s["session_id"])),
            reverse=True,
        )

    sessions: list[dict[str, Any]] = []
    prompts_sampled = 0
    prompts_available = sum(s["prompt_count"] for s in available_sessions)
    for session in available_sessions:
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
        prompts_sampled += session["prompt_count"]
        sessions.append(session)

    dossier["sessions"] = sessions
    dossier["sessions_found"] = len(available_sessions)
    dossier["sessions_graded"] = len(sessions)
    dossier["sessions_scanned"] = len(available_sessions)
    dossier["prompts_sampled"] = prompts_sampled
    dossier["prompts_available"] = prompts_available
    dossier["redaction_notes"] = notes
    return attach_efficiency(dossier)


def _content_to_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") in ("text", "input_text", "output_text"):
                parts.append(str(block.get("text", "")))
        text = "\n".join(p for p in parts if p)
        return text or None
    return None


_CORRECTION_RE = re.compile(
    r"(?i)\b(no,|wrong|not what i|i meant|actually,|fix:|that's incorrect)\b"
)
_ABORT_RE = re.compile(r"(?i)\b(never ?mind|cancel that|abort|stop working on this)\b")


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_signals(user_prompts: list[str], assistant_questions: int = 0) -> dict[str, Any]:
    # corrections: user pushes back on misunderstanding (see signals.md)
    corrections = sum(1 for p in user_prompts if _CORRECTION_RE.search(p))
    # restates: high token Jaccard + similar length vs previous prompt
    restates = 0
    for i in range(1, len(user_prompts)):
        prev, cur = user_prompts[i - 1], user_prompts[i]
        if _jaccard(_tokens(prev), _tokens(cur)) >= 0.8:
            if abs(len(prev) - len(cur)) <= max(10, int(0.3 * max(len(prev), len(cur)))):
                restates += 1
    # clarify_loops: assistant asked 2+ questions; user replies still short/vague
    clarify_loops = 0
    if assistant_questions >= 2:
        clarify_loops = sum(1 for p in user_prompts if len(p.strip()) < 40)
    # abandoned_goal: explicit abort language or abrupt short final prompt
    abandoned = False
    if user_prompts and _ABORT_RE.search(user_prompts[-1]):
        abandoned = True
    elif len(user_prompts) >= 3 and len(user_prompts[-1].strip()) < 12:
        abandoned = True
    return {
        "corrections": corrections,
        "restates": restates,
        "clarify_loops": clarify_loops,
        "abandoned_goal": abandoned,
    }


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


def segment_tasks_by_session(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Segment tasks within each session independently.

    Unlike attach_efficiency's flat approach, a task never spans two sessions.
    Each returned task carries its originating session_id.
    """
    tasks: list[dict[str, Any]] = []
    for session in sessions:
        sid = session.get("session_id", "")
        prompts = session.get("user_prompts") or []
        for task in segment_tasks(prompts):
            task = dict(task)
            task["session_id"] = sid
            tasks.append(task)
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


def parse_session_jsonl(path: Path) -> dict[str, Any]:
    prompts: list[str] = []
    times: list[str] = []
    session_id = path.stem
    redaction_notes: list[str] = []
    assistant_questions = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("sessionId"):
                session_id = ev["sessionId"]
            if ev.get("type") == "assistant":
                msg = ev.get("message") or {}
                text = _content_to_text(msg.get("content"))
                if text and "?" in text:
                    assistant_questions += 1
            text = None
            if ev.get("type") == "user":
                origin = ev.get("origin") or {}
                if origin and origin.get("kind") not in (None, "human"):
                    continue
                msg = ev.get("message") or {}
                if msg.get("role") != "user":
                    continue
                text = _content_to_text(msg.get("content"))
            elif ev.get("type") == "queue-operation" and ev.get("operation") == "enqueue":
                text = ev.get("content") if isinstance(ev.get("content"), str) else None
            if not text or not str(text).strip():
                continue
            cleaned, notes = redact_secrets(str(text))
            cleaned, tnotes = truncate_prompt(cleaned)
            redaction_notes.extend(n for n in notes + tnotes if n not in redaction_notes)
            if prompts and prompts[-1] == cleaned:
                continue
            prompts.append(cleaned)
            if ev.get("timestamp"):
                times.append(ev["timestamp"])
    project_path = path.parent.name
    if path.parent.name == "sessions":
        project_path = path.parent.parent.name
    return {
        "session_id": session_id,
        "project_path": project_path,
        "started_at": times[0] if times else None,
        "ended_at": times[-1] if times else None,
        "user_prompts": prompts,
        "prompt_count": len(prompts),
        "signals": compute_signals(prompts, assistant_questions),
        "_redaction_notes": redaction_notes,
    }


def parse_session_turns(path: Path) -> dict[str, Any]:
    """Return ordered user+assistant turns from a Claude session JSONL file."""
    from datetime import datetime, timezone

    fallback_ts = datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    ).isoformat()
    session_id = path.stem
    turns: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("sessionId"):
                session_id = ev["sessionId"]
            role: str | None = None
            text: str | None = None
            if ev.get("type") == "user":
                origin = ev.get("origin") or {}
                if origin and origin.get("kind") not in (None, "human"):
                    continue
                msg = ev.get("message") or {}
                if msg.get("role") != "user":
                    continue
                text = _content_to_text(msg.get("content"))
                role = "user"
            elif ev.get("type") == "assistant":
                msg = ev.get("message") or {}
                text = _content_to_text(msg.get("content"))
                role = "assistant"
            if not role or not text or not str(text).strip():
                continue
            ts = ev.get("timestamp") or fallback_ts
            turns.append({
                "role": role,
                "text": str(text).strip(),
                "timestamp": ts,
            })
    return {
        "session_id": session_id,
        "started_at": turns[0]["timestamp"] if turns else None,
        "turns": turns,
    }
