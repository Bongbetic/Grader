"""Static declaration of what each intake adapter can reliably extract.

A capability is True only when the adapter provides it reliably today. Cells
that are False force analysis_eligible=False for features that need them,
rather than letting downstream code guess structure.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterCapability:
    role: bool             # can distinguish user vs assistant vs tool turns
    session_boundary: bool # yields stable session_id boundaries
    assistant_text: bool   # preserves assistant turn text
    timestamp: bool        # yields per-turn or per-session timestamps
    workflow_markers: bool  # surfaces slash/command/skill markers
    tool_outputs: bool     # preserves tool-call outputs for attribution


_ALL_FALSE = AdapterCapability(False, False, False, False, False, False)

CAPABILITY_MATRIX: dict[str, AdapterCapability] = {
    # Claude: per-file sessions; discover_turns preserves user + assistant turns.
    "claude": AdapterCapability(
        role=True, session_boundary=True, assistant_text=True,
        timestamp=True, workflow_markers=True, tool_outputs=True,
    ),
    "cursor": AdapterCapability(
        role=True, session_boundary=True, assistant_text=True,
        timestamp=True, workflow_markers=False, tool_outputs=False,
    ),
    "codex": AdapterCapability(
        role=True, session_boundary=True, assistant_text=True,
        timestamp=True, workflow_markers=False, tool_outputs=True,
    ),
    "copilot": AdapterCapability(
        role=False, session_boundary=False, assistant_text=False,
        timestamp=False, workflow_markers=False, tool_outputs=False,
    ),
    "import_paste": AdapterCapability(
        role=False, session_boundary=False, assistant_text=False,
        timestamp=False, workflow_markers=False, tool_outputs=False,
    ),
}


def capabilities_for(tool: str) -> AdapterCapability:
    return CAPABILITY_MATRIX.get(tool, _ALL_FALSE)


def supports_session_analysis(tool: str) -> bool:
    cap = capabilities_for(tool)
    return cap.role and cap.session_boundary
