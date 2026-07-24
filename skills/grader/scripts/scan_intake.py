"""CLI to scan allowlisted intake sources and print a summary."""
from __future__ import annotations

import argparse
import json
import sys

import allowlist
import grader_lib
from adapters import claude as claude_ad
from adapters import codex as codex_ad
from adapters import cursor as cursor_ad
from adapters import copilot as copilot_ad


TOOL_ADAPTERS = {
    "claude": claude_ad,
    "codex": codex_ad,
    "cursor": cursor_ad,
    "copilot": copilot_ad,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan allowlisted intake sources")
    parser.add_argument(
        "--tools",
        default="claude",
        help="Comma-separated list of tools to scan (default: claude)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=grader_lib.DEFAULT_SESSION_LIMIT,
        help=(
            "Maximum recent session files to scan per tool "
            f"(default: {grader_lib.DEFAULT_SESSION_LIMIT})"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON",
    )
    args = parser.parse_args(argv)

    requested = [t.strip() for t in args.tools.split(",") if t.strip()]
    all_results: list[dict] = []
    intake_by_tool: dict[str, dict] = {}
    copilot_partial = False
    for tool in requested:
        if tool not in allowlist.ALLOWLISTED_TOOLS:
            continue
        adapter = TOOL_ADAPTERS.get(tool)
        if adapter is None:
            continue
        try:
            intake_by_tool[tool] = adapter.intake_stats(limit=args.limit)
            tool_results = adapter.discover(limit=args.limit)
            all_results.extend(tool_results)
            if tool == "copilot":
                copilot_results = [
                    r for r in tool_results if r.get("source_tool") == "copilot"
                ]
                if copilot_ad.scan_summary(copilot_results).get("partial"):
                    copilot_partial = True
        except PermissionError as exc:
            payload = {
                "error": "consent_required",
                "tool": tool,
                "message": str(exc),
            }
            if args.json:
                print(json.dumps(payload, sort_keys=True), file=sys.stderr)
            else:
                print(
                    f"Error: consent required for {tool}: {exc}",
                    file=sys.stderr,
                )
            return 2

    summary = claude_ad.scan_summary(all_results, intake=intake_by_tool)
    if copilot_partial:
        summary["partial"] = True
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(f"Total candidates: {summary['total']}")
        for t in summary["tools"]:
            line = f"  {t['tool']}: {t['count']}"
            if "sessions_found" in t:
                line += (
                    f" (sessions {t['sessions_scanned']}/{t['sessions_found']}"
                    f" @ limit {t['session_limit']}"
                )
                if "prompts_discovered" in t:
                    line += f"; prompts {t.get('prompts_in_scan', t['count'])}/{t['prompts_discovered']}"
                line += ")"
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
