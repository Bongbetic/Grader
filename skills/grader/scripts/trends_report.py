#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trends import compute_trends


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print local Grader trends.")
    parser.add_argument(
        "--root", type=Path, default=None, help="Override grader home path."
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit full trends as JSON."
    )
    args = parser.parse_args(argv)

    result = compute_trends(root=args.root)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if not result["available"]:
        print("Trends not yet available. Grade at least two prompts or collect metrics across two periods.")
        return 0

    print(f"Trends available: {result['available']}")
    if result["most_frequent_failing"]:
        mf = result["most_frequent_failing"]
        print(f"Most frequent failing dimension: {mf['dimension_id']} (count: {mf['count']})")
    print(f"Consecutive A/B band streak: {result['streaks']['consecutive_ab_bands']}")
    print(f"Consecutive practice-day streak: {result['streaks']['consecutive_practice_days']}")
    print(f"Band history: {', '.join(p['band'] for p in result['bands_over_time'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
