"""Acceptance smoke test for Grader v3.

- Imports every v3 module.
- Verifies score_math is deterministic over random applicable score sets.
- Verifies retention + trends integration on a temporary grader home.
"""

from __future__ import annotations

import importlib
import random
from datetime import datetime, timedelta, timezone

import pytest

_V3_MODULES = [
    "domain",
    "score_math",
    "redact",
    "paths",
    "consent",
    "store",
    "retention",
    "allowlist",
    "adapters",
    "adapters.claude",
    "adapters.codex",
    "adapters.cursor",
    "adapters.copilot",
    "adapters.import_paste",
    "normalize",
    "model_class",
    "judge_schema",
    "teaching",
    "curriculum",
    "trends",
    "trends_report",
    "practice_session",
    "scan_intake",
    "finalize_grade",
    "purge_data",
]


@pytest.mark.parametrize("module_name", _V3_MODULES)
def test_import_v3_module(module_name: str) -> None:
    importlib.import_module(module_name)


def test_score_math_is_stable_for_random_applicable_scores() -> None:
    from domain import DIMENSION_WEIGHTS, DimensionScore, NA
    from score_math import finalize

    random.seed(42)
    for _ in range(20):
        scores: list[DimensionScore] = []
        for dim_id, weight in DIMENSION_WEIGHTS.items():
            if dim_id in ("D8", "D9", "D10", "D11"):
                level = random.choice([0, 1, 2, 3, NA])
            else:
                level = random.choice([0, 1, 2, 3])
            scores.append(DimensionScore(dim_id, level, weight))

        result = finalize(
            scores, disqualifier_flags=[], target_model_class="standard"
        )
        again = finalize(
            scores, disqualifier_flags=[], target_model_class="standard"
        )
        assert result == again
        earned, possible, percent, band, caps = result
        assert 0.0 <= percent <= 100.0
        assert band in ("A", "B", "C", "D")
        assert possible > 0


def test_retention_and_trends_integration(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GRADER_HOME", str(tmp_path))

    import retention
    import store
    import trends
    from domain import DIMENSION_WEIGHTS, DimensionScore
    from score_math import finalize

    old = datetime.now(timezone.utc) - timedelta(days=31)
    scores = [
        DimensionScore(dim_id, 2, weight)
        for dim_id, weight in DIMENSION_WEIGHTS.items()
    ]
    earned, possible, percent, band, caps = finalize(
        scores, disqualifier_flags=[], target_model_class="standard"
    )
    report = {
        "id": "g1",
        "prompt_id": "p1",
        "dimension_scores": [
            {"dimension_id": s.dimension_id, "level": s.level, "weight": s.weight}
            for s in scores
        ],
        "earned": earned,
        "possible": possible,
        "percent": percent,
        "band": band,
        "caps_applied": caps,
        "ingested_at": old.isoformat(),
    }

    store.save_grade(
        report,
        persist_raw=True,
        raw_text="raw secret example text",
        excerpt="redacted excerpt",
    )
    store.append_trend_metric(
        {"metric_type": "band", "value": band, "period": old.date().isoformat()}
    )

    purged = retention.purge_expired(days=30)
    assert purged >= 1
    assert not (tmp_path / "raw" / "p1.txt").exists()
    assert (tmp_path / "metrics.jsonl").is_file()

    today = datetime.now(timezone.utc).date().isoformat()
    store.append_trend_metric(
        {"metric_type": "band", "value": "B", "period": today}
    )
    result = trends.compute_trends()
    assert result["available"] is True
    assert result["bands_over_time"]
