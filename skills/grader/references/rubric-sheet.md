# Judge-facing rubric sheet

Use this sheet when scoring a single prompt. **You** (the agent running Grader) return only the structured JSON in `judge-schema.json`. Python recomputes the final percent, band, and caps from the levels you provide.

## Dimensions

Score each **applicable** dimension 0–3. Mark conditional dimensions (D8–D11) **N/A** when the task does not trigger them.

### Core dimensions (always scored)

**D1. Objective & Success Criteria — weight ×3**
Is the exact action explicit (lead verb: *write / analyze / extract / build*), and is "done well" defined (acceptance criteria, measurable outcome)?
- 0: Vague ("help with marketing").
- 1: Action stated, no success bar.
- 2: Clear action + rough scope.
- 3: Action + explicit, checkable success criteria.

**D2. Context & Motivation — weight ×2**
Background, purpose, audience, and *why* it matters and how the output will be used.
- 0: None.
- 1: Minimal background.
- 2: Adequate background + audience.
- 3: Background + audience + motivation/use.

**D3. Specificity & Constraints — weight ×2**
Scope boundaries, length, format constraints, must-haves/must-nots, budget/technical limits — and *no contradictions*.
- 0: Open-ended, no constraints.
- 1: One or two constraints.
- 2: Constraints cover the main risks.
- 3: Tight, complete, internally consistent.

**D4. Output Format & Structure — weight ×2**
Is the desired output shape specified (schema, sections, prose-vs-list, delimiters), and does the prompt use delimiters to separate instruction from data?
- 0: Unspecified.
- 1: Loosely implied.
- 2: Format stated.
- 3: Format shown/prefilled + clean instruction–data separation.

**D5. Model & Parameter Fit — weight ×3**
Is the prompt built for the *class* of model that will run it? Reasoning vs standard; effort/verbosity set; no cross-class anti-patterns.
- 0: Mismatched (e.g. forced CoT on a reasoning model, or a bare one-liner sent to a standard model for a hard task).
- 1: Class-agnostic.
- 2: Reasonable fit.
- 3: Explicitly tuned to model class + parameters.
- *Unknown model class:* if the target class cannot be inferred, D5 is not assessable — exclude it from earned and possible (same effect as **N/A**). Do not apply the `wrong_model_class` cap. Prefer marking D5 **N/A** in judge JSON when class is already known `unknown` before scoring; `score_math.finalize` drops D5 either way.

**D6. Economy & Clarity — weight ×2**
Minimum necessary structure; plain unambiguous language; no repetition, no bloat, no dead instructions.
- 0: Bloated or confusing.
- 1: Wordy but followable.
- 2: Clean.
- 3: Lean and unambiguous — passes the "confused colleague" test.

**D7. Testability & Iteration-Readiness — weight ×2**
Can output quality be checked against the stated criteria? Is the prompt structured so one variable can be changed and re-tested? Is it robust rather than brittle?
- 0: No way to judge success.
- 1: Judgeable subjectively.
- 2: Checkable criteria present.
- 3: Checkable + isolable variables + evaluation/iteration plan implied.

### Conditional dimensions (score only if triggered; otherwise N/A)

**D8. Grounding / Reference Material — weight ×3** *(trigger: factual accuracy or domain data matters)*
Is source text/data supplied or retrieved, rather than left to the model's memory?
- 0: Fact-heavy task, no sources.
- 1: Vague reference.
- 2: Relevant sources supplied.
- 3: Sources supplied + scoped to the most relevant (no dump) + citation/uncertainty instruction.

**D9. Examples / Shot Design — weight ×2** *(trigger: format/style/pattern is hard to describe)*
Are examples present where they help, consistent in format, and aligned to the wanted behavior — with model class respected?
- 0: Needed but absent, or examples contradict the ask.
- 1: Present but inconsistent.
- 2: Clear, consistent example(s).
- 3: Minimal-sufficient, consistent, behavior-aligned (and omitted/limited for reasoning models).

**D10. Voice: Persona / Style / Tone / Audience — weight ×2** *(trigger: communication quality matters — copy, comms, teaching)*
Is the perspective/voice specified appropriately for the audience — without over-constraining the persona?
- 0: Voice matters but unspecified.
- 1: Vague ("professional").
- 2: Style + audience specified.
- 3: Style + tone + audience, calibrated and not over-constrained.

**D11. Hallucination / Safety Guards — weight ×2** *(trigger: high-stakes or factual)*
Permission to express uncertainty; instruction to avoid fabrication; self-verification step where warranted.
- 0: None on a high-stakes task.
- 1: Implicit.
- 2: "Say if unsure" present.
- 3: Uncertainty permission + verification/self-check step.

## Scoring procedure

1. Score each **applicable** dimension 0–3; mark conditional dimensions **N/A** when the task does not trigger them.
2. Multiply each score by its weight; sum to get **earned points**.
3. Sum `(3 × weight)` over the **applicable** dimensions to get **possible points**.
4. When `target_model_class` is `unknown`, exclude D5 from both earned and possible (AS-005). Suppress `wrong_model_class`.
5. **Score % = earned / possible × 100.**
6. Apply any **disqualifier caps**, taking the lower of the computed grade and the cap.

## Grade bands

| % | Grade | Meaning | Action |
|---|---|---|---|
| 90–100 | **A** | No material ambiguity; ready to run | Ship / execute |
| 75–89 | **B** | Minor gaps; light iteration | One clarifying pass |
| 60–74 | **C** | Real gaps the writer must fill | Return with targeted questions |
| < 60 | **D** | Under-specified; rebuild | Guided rewrite from D1 |

## Disqualifier caps

These cap the final grade to **C** regardless of raw percentage. Set the corresponding flag in the `disqualifiers` array using the exact `DISQUALIFIER_IDS` from `domain.py`:

- `forced_cot_on_reasoning` — explicit "think step by step" sent to a reasoning model.
- `internal_contradiction` — instructions contradict each other.
- `complex_task_d1_zero` — complex/multi-step task with D1 = 0.
- `fact_critical_d8_zero` — fact-critical task with D8 = 0 when triggered.
- `wrong_model_class` — prompt aimed at the wrong model class (D5 = 0). Suppressed when target class is `unknown`.

## Quick scoring sheet

```text
Task type: ____________________   Target model class: [ ] standard  [ ] reasoning  [ ] unknown

CORE                              score(0-3)  ×w   = pts
D1 Objective & success criteria   [   ]       ×3   ____
D2 Context & motivation           [   ]       ×2   ____
D3 Specificity & constraints      [   ]       ×2   ____
D4 Output format & structure      [   ]       ×2   ____
D5 Model & parameter fit          [   ]       ×3   ____
D6 Economy & clarity              [   ]       ×2   ____
D7 Testability & iteration        [   ]       ×2   ____

CONDITIONAL (N/A if untriggered)
D8 Grounding / reference          [   ]       ×3   ____
D9 Examples / shot design         [   ]       ×2   ____
D10 Voice (persona/style/tone/aud)[   ]       ×2   ____
D11 Hallucination / safety guards [   ]       ×2   ____

Earned pts ____ / Possible pts ____  =  ____%   Grade: ____
Disqualifier caps applied? ________   Final grade: ____
```

## Teaching layer — turning a low score into a fix

- **D1 low →** "What does a perfect result look like, and how would you check it?" Add a one-line acceptance test.
- **D2 low →** State the audience and *why* you need this; the "why" lets the model resolve edge cases you didn't foresee.
- **D3 low →** Add scope boundaries and one length/format constraint; then scan for any two instructions that fight each other.
- **D4 low →** Show the shape you want (a two-line skeleton or JSON stub) instead of describing it; separate your instructions from your data.
- **D5 low →** Decide the model class first. Standard model + hard task → add reasoning scaffolding. Reasoning model → strip CoT and examples, set the effort level.
- **D6 low →** Cut every sentence that doesn't change the output. Read it as a stranger would.
- **D7 low →** Write the pass/fail check *before* running; change one thing at a time when iterating.
- **D8 low →** Paste the source material (scoped, not dumped) rather than trusting recall; ask for citations.
- **D9 low →** Add one aligned example; only add a second if output still drifts; keep example format identical.
- **D10 low →** Name style, tone, and audience separately (CO-STAR's insight); avoid caricature personas.
- **D11 low →** Add "If you're unsure or the data is insufficient, say so rather than guessing," plus a verification step for high-stakes output.

## Classification & attribution (judge instructions)

Before scoring dimensions, emit a `classification` block. **`task_complexity` and
`prompt_class` are required** for every scored prompt (abstain on `prompt_class`
only when the transcript truly does not support a confident call). Every entry needs a
verbatim evidence span from the redacted transcript (`evidence_span` field) and a `confidence`
(low/medium/high). When the transcript does not support a confident call,
**abstain** — use `indeterminate` (rework_cause) or omit the optional field.

- **Task complexity** — `trivial | simple | moderate | complex`. Drives the
  proportionality lens: score D1/D3 against the investment this complexity
  foreseeably warrants, not an absolute maximum. Terse on a trivial task is not
  a defect.
- **prompt_class** — `standalone | valid_continuation | lazy_delegation |
  execution_handoff_gap | workflow_protocol_reply`. A `workflow_protocol_reply`
  (a gate answer like "approved"/"look again" the workflow solicited) is NOT
  prompt craft — do not score it.
- **rework_cause** — attribute any restate/correction to a cause:
  `user_under_specified | agent_misread | tool_or_environment | new_information
  | user_preference_change | indeterminate`. **Only `user_under_specified` at
  high confidence reflects the user's prompt craft.** Agent misreads, tool
  errors, new information, and preference changes are NOT user failures and must
  never lower a grade.

Deterministic restate/correction counts are candidate signals only; your
attributed classification is the verdict.

## Proportionality lens (applies to D1, D3, D6; D2 when `valid_continuation`)

Score D1/D3/D6 against the **foreseeable need** implied by `task_complexity`, not an
absolute maximum:

- Terse on a trivial/simple task → do not dock D1/D3/D6 for brevity. A one-liner can score well.
- Terse on a moderate/complex task where structure would foreseeably have helped
  → dock D1/D3 and set the flag `underinvested_for_task`. This flag is evidence
  only; it does not cap. It records that the prompt left proportional upside on
  the table.
- **D6:** reward economy when the prompt is appropriately lean for the complexity;
  do not penalize a terse prompt that still meets the foreseeable need.

**D2 — valid continuations.** When `prompt_class` is `valid_continuation` and prior
user turns already supply audience, motivation, or repo context, score D2
**proportionally** — level 2 is appropriate when context is implicit in the
session (e.g. "commit and push" after a full change list). Do not zero D2 or
treat missing repeated background as a defect. Reserve D2 = 0–1 for
`lazy_delegation` or standalone prompts that truly lack context.

This is the "was there upside left on the table?" test, not "did the agent cope anyway?"

## Convention checklists

**D4 — structure conventions.** Reward: role/context/task/format completeness
(PTCF), delimiters separating instruction from data, format shown not described,
positive format control ("say what to do"). These key on class-level principles,
not brand idioms.

**D5 — model-class divergence.** Pin the target class first, then apply the
divergence:
- Standard model + hard task → reward reasoning scaffolding / chain-of-thought.
- Reasoning model → penalize explicit "think step by step" and few-shot (they
  degrade it); reward lean prompt + effort/verbosity parameters.
- Do not reward brand-specific tag gimmicks (e.g. mandatory XML) — deprecated as a default.
