from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

DEFAULT_SESSION_LIMIT = 30

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


def parse_session_jsonl(path: Path) -> dict[str, Any]:
    prompts: list[str] = []
    times: list[str] = []
    session_id = path.stem
    redaction_notes: list[str] = []
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
            redaction_notes.extend(n for n in notes if n not in redaction_notes)
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
        "signals": {
            "corrections": 0,
            "restates": 0,
            "clarify_loops": 0,
            "abandoned_goal": False,
        },
        "_redaction_notes": redaction_notes,
    }
