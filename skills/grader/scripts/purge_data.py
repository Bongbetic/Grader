from __future__ import annotations

import argparse
import sys
from pathlib import Path

import retention


def _parse_what(value: str) -> set[str]:
    parts = {p.strip() for p in value.split(",") if p.strip()}
    if not parts.issubset(retention._ALLOWED_PURGE):
        raise ValueError(f"--what must be subset of {retention._ALLOWED_PURGE}")
    return parts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Purge stored Grader data.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--expired", action="store_true", help="Purge grade records older than retention days.")
    group.add_argument("--user", action="store_true", help="Purge user-selected data categories.")
    parser.add_argument("--what", default="", help="Comma-separated categories for --user: raw,excerpts,metrics,consent,all")
    parser.add_argument("--days", type=int, default=30, help="Retention window in days for --expired (default: 30).")
    parser.add_argument("--root", type=Path, default=None, help="Override grader home path.")
    args = parser.parse_args(argv)

    if args.expired:
        count = retention.purge_expired(root=args.root, days=args.days)
        print(count)
        return 0

    if args.user:
        if not args.what:
            parser.error("--what is required with --user")
        try:
            what = _parse_what(args.what)
        except ValueError as exc:
            parser.error(str(exc))
        retention.user_purge(root=args.root, what=what)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
