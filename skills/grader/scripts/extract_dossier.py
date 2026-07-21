#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grader_lib import (
    DEFAULT_SESSION_LIMIT,
    build_dossier_from_claude_root,
    build_dossier_from_export,
    resolve_claude_root,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract Claude Code prompt dossier")
    p.add_argument("--root", type=Path, default=None, help="Claude config root override")
    p.add_argument("--limit", type=int, default=DEFAULT_SESSION_LIMIT)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--export", type=Path, default=None, help="Path to /export or paste file")
    args = p.parse_args(argv)

    if args.export is not None:
        if not args.export.exists():
            print(f"Export file not found: {args.export}", file=sys.stderr)
            return 2
        text = args.export.read_text(encoding="utf-8")
        dossier = build_dossier_from_export(text, intake_path="export")
        if dossier["sessions_graded"] == 0:
            print("No sessions found to grade", file=sys.stderr)
            return 2
        output = json.dumps(dossier, indent=2, ensure_ascii=False)
        if args.out:
            args.out.write_text(output, encoding="utf-8")
        else:
            print(output)
        return 0

    root = args.root if args.root is not None else resolve_claude_root()
    if not root.exists():
        print(f"Claude config root not found: {root}", file=sys.stderr)
        return 2
    dossier = build_dossier_from_claude_root(root, limit=args.limit)
    if dossier["sessions_graded"] == 0:
        print("No sessions found to grade", file=sys.stderr)
        return 2
    text = json.dumps(dossier, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
