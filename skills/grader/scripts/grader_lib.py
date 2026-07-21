from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

DEFAULT_SESSION_LIMIT = 30
MAX_PROMPT_CHARS = 4000
_TRUNCATED_SUFFIX = " …[truncated]"

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("generic_bearer", re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
]


def redact_secrets(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(out):
            out = pattern.sub("[REDACTED_SECRET]", out)
            if label not in notes:
                notes.append(label)
    return out, notes


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
    claude_root: Path, limit: int = DEFAULT_SESSION_LIMIT
) -> dict[str, Any]:
    found = discover_session_files(claude_root)
    selected = select_recent_sessions(found, limit=limit)
    dossier = empty_dossier("auto")
    dossier["sessions_found"] = len(found)
    notes: list[str] = []
    sessions = []
    for path in selected:
        session = parse_session_jsonl(path)
        if session["prompt_count"] == 0:
            continue
        for n in session.pop("_redaction_notes", []):
            if n not in notes:
                notes.append(n)
        sessions.append(session)
    dossier["sessions"] = sessions
    dossier["sessions_graded"] = len(sessions)
    dossier["redaction_notes"] = notes
    return dossier


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


def build_dossier_from_export(text: str, intake_path: str = "export") -> dict[str, Any]:
    dossier = empty_dossier(intake_path)
    chunks = [c.strip() for c in re.split(r"(?im)^##\s+session\b[^\n]*$", text) if c.strip()]
    if not chunks:
        chunks = [text]
    notes: list[str] = []
    sessions = []
    for i, chunk in enumerate(chunks):
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
        sessions.append({
            "session_id": f"export-{i+1}",
            "project_path": "export",
            "started_at": None,
            "ended_at": None,
            "user_prompts": prompts,
            "prompt_count": len(prompts),
            "signals": compute_signals(prompts, assistant_qs),
        })
    dossier["sessions"] = sessions
    dossier["sessions_found"] = len(sessions)
    dossier["sessions_graded"] = len(sessions)
    dossier["redaction_notes"] = notes
    return dossier


def _content_to_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
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
