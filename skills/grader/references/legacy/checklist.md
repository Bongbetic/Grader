# Grader checklist

Distilled rubric for **historical user prompts in Claude Code** (not API system-prompt engineering). Grade the aggregate of the sampled sessions, not a single prompt.

## Dimensions

Score each dimension **applicable** to the dossier. Use evidence snippets from `user_prompts[]`.

## Per-dimension verdicts

Use this scale for each dimension. Mark **N/A** only when the dimension genuinely does not apply; otherwise choose the closest supported verdict.

### 1. Clarity & directness

Explicit ask; unambiguous outcome. The reader (and agent) can tell what action or deliverable is requested without guessing.

- **Strong:** concrete verbs, named artifacts, clear scope in the first prompt.
- **Adequate:** the ask is understandable, but scope, artifact names, or first-step intent are partial or uneven.
- **Weak:** vague imperatives (“fix it”, “make it better”), pronouns without referents, multiple possible interpretations.
- **N/A:** almost never; use only when no actionable request is being graded.

### 2. Context & motivation

Why constraints exist when it matters — background, stack, prior decisions, or user goal that shapes the right answer.

- **Strong:** relevant file paths, error messages, constraints tied to a goal.
- **Adequate:** some useful context appears, but key motivation, environment, or prior-decision details are partial or uneven.
- **Weak:** task stated with no situational context when context would change the approach.
- **N/A:** context would not change the approach for the sampled prompts.

### 3. Success criteria

What “done” means — observable outcomes, acceptance checks, or explicit definition of correct behavior.

- **Strong:** “passes these tests”, “matches this API shape”, “user can log in with magic link”.
- **Adequate:** a likely finish line is implied, but acceptance checks or observable behavior are partial or uneven.
- **Weak:** no way to verify completion; open-ended “just make it work” without a finish line.
- **N/A:** the sampled ask is exploratory or advisory and has no meaningful completion check.

### 4. Structure

Steps when order matters; instructions separated from data; readable layout for multi-part asks.

- **Strong:** numbered steps, labeled sections, pasted code/logs separated from instructions.
- **Adequate:** readable enough to follow, but sequencing, labels, or data separation are partial or uneven.
- **Weak:** wall of text mixing requirements and raw dumps; critical ordering left implicit.
- **N/A:** the sampled prompt is atomic enough that extra structure would not help.

### 5. Constraints & boundaries

Scope, must/must-not, safety/agentic limits — what to touch, what to avoid, time/scope bounds.

- **Strong:** “only change `auth.ts`”, “do not commit”, “no new dependencies”.
- **Adequate:** some boundaries are present, but risky scope, ownership, or agentic limits are partial or uneven.
- **Weak:** unbounded “refactor everything” or missing guardrails on risky operations.
- **N/A:** the task has no meaningful risky scope or boundary decisions.

### 6. Examples (when format/judgment matters)

Reference examples when output format, style, or judgment consistency matters.

- **Strong:** sample input/output, prior art, or “like X but with Y”.
- **Adequate:** examples or references exist, but coverage, format specificity, or relevance is partial or uneven.
- **Weak:** format-sensitive request with no exemplar when ambiguity is high.
- **N/A:** when the task is fully specified without format ambiguity.

### 7. Agentic hygiene

Proportionate scope; avoid over-eager or test-gaming instructions; state boundaries for long runs.

- **Strong:** right-sized tasks, honest constraints, no “ignore tests” or “ship at all costs”.
- **Adequate:** autonomy is mostly reasonable, but checkpoints, scope sizing, or safety boundaries are partial or uneven.
- **Weak:** contradictory autonomy (“do everything” + “don’t change anything”), gaming evals, unbounded agent loops without checkpoints.
- **N/A:** almost never; use only when the sampled prompts do not delegate work to an agent.

### 8. Cross-session consistency

Stable constraints and style across the sample; flag contradictory habits without reason.

- **Strong:** similar tasks get similar level of detail and constraints.
- **Adequate:** broadly stable prompting habits with a few unexplained or uneven shifts.
- **Weak:** same project/context treated inconsistently (detailed specs in one session, one-liners in the next) without explanation.
- **N/A:** only one usable session or insufficient comparable cross-session evidence.

## N/A rules

- Mark a dimension **N/A** when it genuinely does not apply to the sampled prompts (e.g. no multi-step workflows → Structure may be N/A for a single atomic ask).
- **N/A never lowers the grade.** Exclude N/A dimensions from the denominator when assessing overall craft.
- Do not mark N/A to avoid noting a real gap.

## Letter scale (aggregate)

| Grade | Meaning |
|-------|---------|
| **A** | Consistently clear, contextualized, well-scoped prompts; few correction/restatement loops; applicable checklist mostly satisfied; no material cross-session contradictions |
| **B** | Strong overall; recurring soft spots (e.g. missing success criteria, uneven structure) or mild inconsistency; some clarify/correct loops |
| **C** | Frequent vagueness, missing constraints/context, or clear craft↔signal mismatch (weak prompts *and* heavy correction loops) |
| **D** | Habitual under-specification or contradictory prompting; signals show repeated failure to steer; foundational gaps dominate |

## Letter derivation rule

Derive the **Skill** letter from applicable, non-N/A verdicts:

- Mostly **Strong** verdicts imply the A/B band; use **A** when strengths are consistent and material gaps are rare, **B** when strengths dominate but soft spots recur.
- A mixed profile of **Strong**, **Adequate**, and occasional **Weak** verdicts implies the B/C band, depending on whether the gaps affect core task steerability.
- Mostly **Weak** verdicts imply the C/D band; use **D** only when foundational craft failures or contradictions dominate the dossier.
- Cross-session consistency gaps can lower the provisional Skill letter one step when contradictions are material and unexplained.
- Signal modifiers can lower the Skill letter at most one additional step under `signals.md` rules, and only when corroborated by checklist craft gaps.
- The separate **Efficiency** score does **not** change the Skill letter directly; report Skill, Efficiency, and Consistency as distinct axes.

## Score axes

- **Skill:** checklist-based prompting craft, represented by the A-D letter after consistency and allowed signal modifiers.
- **Efficiency:** conversation efficacy such as prompts-per-task, single-shot completion, and rework rates; never token, cost, latency, cache, or model-tier efficiency.
- **Consistency:** stability of prompting habits and constraints across sampled sessions; it can affect Skill through the consistency rule above and should also be reported explicitly.

## DNA id mapping

| Dimension display name | `dna.id` |
|------------------------|----------|
| Clarity & directness | `clarity` |
| Context & motivation | `context` |
| Success criteria | `success_criteria` |
| Structure | `structure` |
| Constraints & boundaries | `constraints` |
| Examples | `examples` |
| Agentic hygiene | `agentic_hygiene` |
| Cross-session consistency | `cross_session_consistency` |

## Decision order

Apply in this order; do not skip steps.

1. **Checklist** — Score applicable dimensions on the dossier; identify primary gap themes with evidence.
2. **Consistency** — Assess cross-session contradictions; note and possibly cap the letter when contradictory habits appear without reason.
3. **Signal modifiers** — Apply lightly per `signals.md` (may pull down one letter only when corroborated by craft gaps).
4. **Emit distinct axes** — Skill letter (A-D) plus separate Efficiency and Consistency reporting with structured feedback.

## Never inflate

Polish, politeness, or length do **not** raise a grade built on chronic under-specification. A verbose but vague sample remains weak. Grade on craft and efficacy, not eloquence.
