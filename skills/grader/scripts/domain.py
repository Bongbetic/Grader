from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TargetModelClass = Literal["standard", "reasoning", "unknown"]
GradeBand = Literal["A", "B", "C", "D"]
DimensionId = Literal["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11"]
NA: Literal["N/A"] = "N/A"

CORE_DIMENSIONS: tuple[str, ...] = ("D1", "D2", "D3", "D4", "D5", "D6", "D7")
CONDITIONAL_DIMENSIONS: tuple[str, ...] = ("D8", "D9", "D10", "D11")
DIMENSION_WEIGHTS: dict[str, int] = {
    "D1": 3, "D2": 2, "D3": 2, "D4": 2, "D5": 3, "D6": 2, "D7": 2,
    "D8": 3, "D9": 2, "D10": 2, "D11": 2,
}
DISQUALIFIER_IDS = frozenset({
    "forced_cot_on_reasoning",
    "internal_contradiction",
    "complex_task_d1_zero",
    "fact_critical_d8_zero",
    "wrong_model_class",
})


@dataclass(frozen=True)
class DimensionScore:
    dimension_id: str
    level: int | Literal["N/A"]
    weight: int

    def __post_init__(self) -> None:
        if self.dimension_id not in DIMENSION_WEIGHTS:
            raise ValueError(f"unknown dimension_id: {self.dimension_id}")
        if self.level is None:
            raise ValueError("level must be 0-3 or N/A, not null")
        if self.level != NA and self.level not in (0, 1, 2, 3):
            raise ValueError(f"invalid level: {self.level}")
        if self.weight != DIMENSION_WEIGHTS[self.dimension_id]:
            raise ValueError("weight must match DIMENSION_WEIGHTS")


@dataclass
class PromptRecord:
    id: str
    prompt_text: str | None
    redacted_text: str
    redacted_excerpt: str
    source_tool: str
    timestamp: str
    target_model_class: TargetModelClass
    redaction_flags: list[str] = field(default_factory=list)
    persist_raw: bool = False


TurnRole = Literal["user", "assistant", "tool"]


@dataclass
class TurnRecord:
    source_tool: str
    session_id: str
    turn_index: int
    role: TurnRole
    timestamp: str
    text_redacted: str
    model_id: str | None = None
    workflow_marker: str | None = None
    parser_confidence: float = 1.0
    analysis_eligible: bool = True

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant", "tool"):
            raise ValueError(f"invalid role: {self.role}")
        if self.turn_index < 0:
            raise ValueError("turn_index must be >= 0")
        if not (0.0 <= self.parser_confidence <= 1.0):
            raise ValueError("parser_confidence must be in [0.0, 1.0]")


@dataclass
class GradeReport:
    id: str
    prompt_id: str
    dimension_scores: list[DimensionScore]
    earned: float
    possible: float
    percent: float
    band: GradeBand
    caps_applied: list[str]
    rationales: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.percent <= 100.0):
            raise ValueError("percent out of range")
        if self.band not in ("A", "B", "C", "D"):
            raise ValueError("invalid band")


@dataclass
class EfficacyReport:
    session_id: str
    prompts_per_task_mean: float
    single_shot_rate: float
    attributed_rework_rate: float   # rework attributed to user_under_specified only
    worst_task_prompt_count: int
    restates: int
    corrections: int
    abandoned_goal: bool


@dataclass
class PlanningReport:
    session_id: str
    planned_decomposition: int
    additive_feature: int
    adaptive_change_with_evidence: int
    scope_change_without_prior_signal: int
    under_specified_initial_plan: int


@dataclass
class TaskReport:
    session_id: str
    opening_prompt_id: str
    craft_band: GradeBand
    efficacy: EfficacyReport
    planning: PlanningReport
    classifier_version: str
    evidence_spans: list[str] = field(default_factory=list)
