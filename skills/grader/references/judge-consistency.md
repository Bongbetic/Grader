# Judge consistency policy

Grader is **model agnostic** in a specific, bounded sense. This document is the contract for learners, hosts, and maintainers.

## Two layers

| Layer | What it does | Host-model independent? |
|-------|----------------|-------------------------|
| **Deterministic (Python)** | Weighted percent, letter band, disqualifier caps, outcome-modifier gate (κ), render (`finalize_grade.py`, `score_math.py`, renderers) | **Yes** — same judge JSON + `target_model_class` always yields the same percent, band, and caps |
| **Stochastic (host judge)** | Dimension levels 0–3, N/A marks, rationales, classification, disqualifier flags | **No** — different judging models may disagree on levels; that is expected |

Learners see one letter grade. The **math and render path** is fixed; **craft scores** come from whichever model runs the skill.

## Learner-facing grades: host-LLM judge JSON only

Every learner-facing grade **must** be produced from **per-prompt host-LLM judge JSON** that conforms to `judge-schema.json`.

**Forbidden for learner-facing grades:**

- Heuristic batch judges (keyword rubrics, regex scorers, dimension-level scripts)
- Automated rubric shortcuts that skip full dimension JSON per prompt
- Reusing one judge template across many prompts without individual review

Heuristic tooling may exist **only** for internal dev calibration. It must **never** substitute for host judge output passed to `finalize_grade.py`.

See also: `flows/grade.md` — **Large intakes (scale playbook)** for sampling rules when intake exceeds 30 prompts (issue #20).

## Deterministic regression

CI holds the math layer stable: fixed judge JSON fixtures under `fixtures/judge/` must always produce the same band and percent from `parse_judge_output` → `build_grade_report` / `finalize_grade.py`. Judge-supplied `percent` and `band` fields are **ignored**; Python always recomputes.

Gold-set cases under `fixtures/gold/` anchor judge **behavior** (proportionality, adversarial floors). They do not replace per-prompt judge JSON at runtime — they calibrate instructions and κ agreement tests.

## D5 and `target_model_class`

**D5 (Model & Parameter Fit)** is scored against the **target model class** (`standard`, `reasoning`, or `unknown`). Divergence rules differ by class (see `rubric-sheet.md` — D5 model-class divergence).

**Cross-class incomparability (by design):** D5 levels are **not comparable across model classes**. A prompt tuned for a reasoning model is judged against reasoning-class expectations; the same text judged under `standard` may earn a different D5 level. Trend comparisons that mix classes without segmenting by `target_model_class` are misleading.

When `target_model_class` is `unknown`, `score_math.finalize` **excludes D5** from earned and possible (AS-005) and suppresses the `wrong_model_class` disqualifier cap. D5 is not assessable without a pinned class.

## Calibration and outcome modifier

- **Gold-set regression** — validates the deterministic math layer (fixed fixtures → stable band).
- **Calibration κ** — gates the outcome modifier (`apply_outcome_modifier`); existing behavior, not redefined here.
- **Fairness anchors** — `fair-terse-valid-continuation` and adversarial gold cases (`adv-fake-criteria`, `adv-contradictory`, `adv-fake-sources`, `adv-useless-plan-trivial`) are referenced in `rubric-sheet.md` so judges apply proportionality and adversarial floors consistently.

## Batch grading at scale

When intake is large, follow the scale playbook in `flows/grade.md`:

1. Default sample ≤ 30 prompts unless the learner opts into the full corpus.
2. **Each sampled prompt** still requires full host-LLM judge JSON — sampling reduces volume, not judge quality.
3. Session rollup uses `--reports-manifest` after per-prompt finalize (see `compose_session_rollup.py`).

No shortcut path may bypass per-prompt judge JSON for grades shown to learners.
