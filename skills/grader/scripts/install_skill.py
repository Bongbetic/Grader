#!/usr/bin/env python3
"""Install the Grader skill for the current coding-agent host."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path

SUPPORTED_HOSTS = ("claude", "cursor", "codex", "copilot")


def skill_destinations(home: Path | None = None) -> dict[str, list[Path]]:
    """Return install destinations per host (first path is primary)."""
    if home is None:
        home = Path.home()
    return {
        "claude": [home / ".claude" / "skills" / "grader"],
        "cursor": [home / ".cursor" / "skills" / "grader"],
        "codex": [
            home / ".codex" / "skills" / "grader",
            home / ".agents" / "skills" / "grader",
        ],
        "copilot": [home / ".github" / "skills" / "grader"],
    }


def detect_host(env: Mapping[str, str] | None = None) -> str | None:
    """Best-effort detection of the coding agent running this installer."""
    env = env if env is not None else os.environ
    if env.get("CURSOR_AGENT") or env.get("CURSOR_TRACE_ID"):
        return "cursor"
    if env.get("CLAUDE_CODE") or env.get("CLAUDE_CODE_SSE_PORT"):
        return "claude"
    if env.get("CODEX_HOME") or env.get("CODEX_INTERNAL"):
        return "codex"
    if env.get("GITHUB_COPILOT") or env.get("COPILOT_AGENT"):
        return "copilot"
    return None


def install(
    source: Path,
    *,
    host: str,
    home: Path | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Copy the skill tree to the host skill directory."""
    if host not in SUPPORTED_HOSTS:
        raise ValueError(f"unsupported host: {host}")
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"missing SKILL.md in {source}")

    installed: list[Path] = []
    for dest in skill_destinations(home)[host]:
        if dry_run:
            installed.append(dest)
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest)
        installed.append(dest)
    return installed


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    skill_dir = here.parent

    parser = argparse.ArgumentParser(
        description="Install Grader for Claude Code, Cursor, Codex, or Copilot",
    )
    parser.add_argument(
        "--host",
        default="auto",
        choices=[*SUPPORTED_HOSTS, "auto", "all"],
        help="Coding-agent host (default: auto-detect)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=skill_dir,
        help="Path to skills/grader (default: this skill directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print destinations without copying",
    )
    args = parser.parse_args(argv)

    if args.host == "auto":
        detected = detect_host()
        if detected is None:
            print(
                "Could not detect host. Pass --host claude|cursor|codex|copilot "
                "or --host all.",
                file=sys.stderr,
            )
            return 2
        hosts = [detected]
        print(f"detected host: {detected}")
    elif args.host == "all":
        hosts = list(SUPPORTED_HOSTS)
    else:
        hosts = [args.host]

    for host in hosts:
        paths = install(args.source, host=host, dry_run=args.dry_run)
        for path in paths:
            action = "would install" if args.dry_run else "installed"
            print(f"{action}: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
