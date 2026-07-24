"""Strip injected boilerplate from learner prompt text before grading."""
from __future__ import annotations

import re

_USER_QUERY_RE = re.compile(
    r"<user_query>\s*(.*?)\s*</user_query>",
    re.DOTALL | re.IGNORECASE,
)

# System-injected context blocks that must not be scored as learner craft.
_BOILERPLATE_TAGS = (
    "manually_attached_skills",
    "agent_skills",
    "mcp_meta_tools",
    "mcp_tool",
    "open_and_recently_viewed_files",
    "git_status",
    "user_info",
    "agent_transcripts",
    "system_reminder",
    "timestamp",
    "hook",
    "hooks",
    "hook_context",
    "subagent",
    "mcp_servers",
)

_BLOCK_PATTERNS = tuple(
    re.compile(rf"<{tag}[^>]*>.*?</{tag}>", re.DOTALL | re.IGNORECASE)
    for tag in _BOILERPLATE_TAGS
)

_MCP_PREAMBLE_RE = re.compile(
    r"(?is)^\s*(?:you have access to mcp|available mcp servers:).*?(?:\n\n|\Z)"
)
_SUBAGENT_PREAMBLE_RE = re.compile(
    r"(?is)^\s*(?:when speaking to the user about which model|"
    r"the user has manually attached the following skills).*?(?:\n\n|\Z)"
)


def _strip_boilerplate_blocks(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    result = text
    for pattern in _BLOCK_PATTERNS:
        new_result = pattern.sub("", result)
        if new_result != result:
            notes.append("stripped_boilerplate_block")
            result = new_result
    return result, notes


def _strip_preamble_lines(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    result = text
    for pattern in (_MCP_PREAMBLE_RE, _SUBAGENT_PREAMBLE_RE):
        new_result = pattern.sub("", result)
        if new_result != result:
            notes.append("stripped_preamble")
            result = new_result
    return result, notes


def _extract_user_query(text: str) -> tuple[str, list[str]]:
    matches = _USER_QUERY_RE.findall(text)
    if not matches:
        return text, []
    cleaned = "\n".join(m.strip() for m in matches if m.strip())
    return cleaned, ["stripped_user_query_tags"]


_WORKFLOW_GATE_REPLIES = frozenset({
    "yes",
    "no",
    "y",
    "n",
    "ok",
    "okay",
    "approve",
    "approved",
    "deny",
    "denied",
    "cancel",
    "continue",
    "proceed",
    "skip",
    "look again",
    "try again",
    "go ahead",
    "looks good",
    "lgtm",
})


def classify_workflow_protocol_reply(text: str) -> bool:
    """Return True when text is a workflow gate reply, not learner craft."""
    normalized = text.strip().lower().rstrip(".!?")
    return normalized in _WORKFLOW_GATE_REPLIES


def sanitize_learner_text(text: str) -> tuple[str, list[str]]:
    """Return learner-authored text with injected transcript boilerplate removed."""
    if not text or not text.strip():
        return text, []

    notes: list[str] = []
    result = text

    result, block_notes = _strip_boilerplate_blocks(result)
    notes.extend(block_notes)

    result, query_notes = _extract_user_query(result)
    notes.extend(query_notes)

    result, preamble_notes = _strip_preamble_lines(result)
    notes.extend(preamble_notes)

    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    notes = list(dict.fromkeys(notes))
    if result and classify_workflow_protocol_reply(result):
        return "", [*notes, "workflow_protocol_reply"]
    return result, notes
