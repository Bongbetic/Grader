#!/usr/bin/env python3
"""One-liner CLI to grant per-tool intake consent."""
from __future__ import annotations

import argparse
import sys

import consent


SUPPORTED_TOOLS = ("claude", "codex", "cursor", "copilot")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grant intake consent for a tool")
    parser.add_argument(
        "--tool",
        required=True,
        choices=SUPPORTED_TOOLS,
        help="Tool to grant consent for",
    )
    args = parser.parse_args(argv)
    consent.grant_consent(args.tool)
    print(f"consent granted: {args.tool}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
