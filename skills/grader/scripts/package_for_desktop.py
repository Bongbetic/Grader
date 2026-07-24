#!/usr/bin/env python3
"""Package skills/grader into a Claude Desktop / claude.ai upload ZIP.

ZIP root must be a single folder named `grader/` containing SKILL.md.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

SKIP_DIR_NAMES = {"__pycache__", ".pytest_cache", ".git"}
SKIP_SUFFIXES = {".pyc"}


def package(skill_dir: Path, out_zip: Path) -> Path:
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"missing SKILL.md in {skill_dir}")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix in SKIP_SUFFIXES:
                continue
            arcname = Path("grader") / path.relative_to(skill_dir)
            zf.write(path, arcname.as_posix())
    return out_zip


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    skill_dir = here.parent  # skills/grader
    p = argparse.ArgumentParser(description="Build grader.zip for Claude Desktop upload")
    p.add_argument(
        "--out",
        type=Path,
        default=skill_dir.parent.parent / "dist" / "grader.zip",
        help="Output zip path (default: repo dist/grader.zip)",
    )
    args = p.parse_args(argv)
    out = package(skill_dir, args.out)
    print(out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
