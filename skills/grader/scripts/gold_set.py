"""Load the human-labeled gold set for calibration."""
from __future__ import annotations

import json
from pathlib import Path


def load_gold(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
