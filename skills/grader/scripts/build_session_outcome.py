"""Build Efficacy and Planning JSON from session-capable tool turns."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

import consent
from capability_matrix import capabilities_for, supports_session_analysis
from domain import TurnRecord
from efficacy import build_efficacy_report
from grader_lib import compute_efficiency, segment_tasks_by_session
from planning import build_planning_report
from turn_intake import build_turn_records

_SESSION_TOOLS = frozenset({"claude", "cursor", "codex"})


def discover_turns_for_tool(
    tool: str,
    *,
    home: Path | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Dispatch ``discover_turns`` to the adapter for a session-capable tool."""
    if tool not in _SESSION_TOOLS:
        raise ValueError(f"unsupported tool for session outcome: {tool}")
    if tool == "claude":
        from adapters import claude as adapter

        return adapter.discover_turns(limit=limit)
    if tool == "cursor":
        from adapters import cursor as adapter

        return adapter.discover_turns(home=home, limit=limit)
    from adapters import codex as adapter

    return adapter.discover_turns(home=home, limit=limit)


def cap_follow_up_confidence(
    labels: dict[tuple[int, int], dict[str, Any]],
    source_tool: str,
) -> dict[tuple[int, int], dict[str, Any]]:
    """Cap ``tool_or_environment`` attribution at medium when tool outputs are absent."""
    if capabilities_for(source_tool).tool_outputs:
        return labels
    capped: dict[tuple[int, int], dict[str, Any]] = {}
    for key, label in labels.items():
        entry = dict(label)
        if (
            entry.get("cause") == "tool_or_environment"
            and entry.get("confidence") == "high"
        ):
            entry["confidence"] = "medium"
        capped[key] = entry
    return capped


def _records_to_sessions(records: list[TurnRecord]) -> list[dict[str, Any]]:
    by_session: dict[str, list[TurnRecord]] = {}
    for record in records:
        if not record.analysis_eligible:
            continue
        by_session.setdefault(record.session_id, []).append(record)

    sessions: list[dict[str, Any]] = []
    for session_id, recs in by_session.items():
        recs.sort(key=lambda r: r.turn_index)
        user_prompts = [r.text_redacted for r in recs if r.role == "user"]
        if not user_prompts:
            continue
        sessions.append(
            {
                "session_id": session_id,
                "user_prompts": user_prompts,
            }
        )
    return sessions


def _efficacy_high_confidence(labels: dict[tuple[int, int], dict[str, Any]]) -> bool:
    for label in labels.values():
        if (
            label.get("value") == "restate_unmet_intent"
            and label.get("cause") == "user_under_specified"
            and label.get("confidence") == "high"
        ):
            return True
    return False


def _planning_high_confidence(labels: list[dict[str, Any]]) -> bool:
    for label in labels:
        if (
            label.get("value") == "under_specified_initial_plan"
            and label.get("confidence") == "high"
        ):
            return True
    return False


def build_session_outcome(
    source_tool: str,
    *,
    session_id: str | None = None,
    follow_up_labels: dict[tuple[int, int], dict[str, Any]] | None = None,
    scope_change_labels: list[dict[str, Any]] | None = None,
    home: Path | None = None,
    limit: int = 100,
    consent_covers_transcript: bool | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Build finalize-ready Efficacy and Planning JSON from adapter turns.

  Returns ``(None, None)`` when the tool lacks session analysis, consent is
  missing, or no analysis-eligible user turns exist for the requested session.
    """
    if not supports_session_analysis(source_tool):
        return None, None
    if not consent.has_consent(source_tool):
        return None, None

    if consent_covers_transcript is None:
        consent_covers_transcript = consent.has_transcript_consent()

    raw_turns = discover_turns_for_tool(source_tool, home=home, limit=limit)
    records = build_turn_records(
        raw_turns,
        source_tool=source_tool,
        consent_covers_transcript=consent_covers_transcript,
    )
    sessions = _records_to_sessions(records)
    if not sessions:
        return None, None

    if session_id is not None:
        matched = [s for s in sessions if s["session_id"] == session_id]
        if not matched:
            return None, None
        session = matched[0]
    else:
        session = sessions[-1]

    tasks = segment_tasks_by_session([session])
    efficiency = compute_efficiency(tasks)

    labels = cap_follow_up_confidence(follow_up_labels or {}, source_tool)
    scope_labels = list(scope_change_labels or [])

    efficacy_report = build_efficacy_report(session["session_id"], efficiency, labels)
    planning_report = build_planning_report(session["session_id"], scope_labels)

    efficacy_json = dataclasses.asdict(efficacy_report)
    efficacy_json["high_confidence_user_underspec"] = _efficacy_high_confidence(labels)

    planning_json = dataclasses.asdict(planning_report)
    planning_json["high_confidence_underspec"] = _planning_high_confidence(scope_labels)

    return efficacy_json, planning_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Efficacy and Planning JSON from session-capable tool turns"
    )
    parser.add_argument(
        "--tool",
        required=True,
        choices=sorted(_SESSION_TOOLS),
        help="Session-capable intake tool",
    )
    parser.add_argument("--session-id", help="Scope outcome to one session id")
    parser.add_argument("--home", type=Path, help="Tool home root for adapter discovery")
    parser.add_argument("--limit", type=int, default=100, help="Max sessions to scan")
    parser.add_argument(
        "--efficacy-out",
        type=Path,
        help="Write efficacy JSON here (stdout JSON object when omitted)",
    )
    parser.add_argument(
        "--planning-out",
        type=Path,
        help="Write planning JSON here (stdout JSON object when omitted)",
    )
    args = parser.parse_args(argv)

    try:
        efficacy, planning = build_session_outcome(
            args.tool,
            session_id=args.session_id,
            home=args.home,
            limit=args.limit,
        )
    except (PermissionError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if efficacy is None or planning is None:
        print("error: no session context available for requested tool/session", file=sys.stderr)
        return 1

    if args.efficacy_out is not None:
        args.efficacy_out.write_text(
            json.dumps(efficacy, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.planning_out is not None:
        args.planning_out.write_text(
            json.dumps(planning, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if args.efficacy_out is None and args.planning_out is None:
        payload = {"efficacy": efficacy, "planning": planning}
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
