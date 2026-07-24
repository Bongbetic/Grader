"""Gate: the outcome band modifier may not run until judge-vs-human agreement
clears the floor recorded in Phase 4 calibration."""
from __future__ import annotations

AGREEMENT_FLOOR = 0.6


def calibration_gate_ok(mean_kappa: float | None) -> bool:
    return mean_kappa is not None and mean_kappa >= AGREEMENT_FLOOR
