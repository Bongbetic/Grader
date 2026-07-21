# Grader checklist

Distilled rubric for **historical user prompts in Claude Code** (not API system-prompt engineering). Grade the aggregate of the sampled sessions, not a single prompt.

## Dimensions

Score each dimension **applicable** to the dossier. Use evidence snippets from `user_prompts[]`.

### 1. Clarity & directness

Explicit ask; unambiguous outcome. The reader (and agent) can tell what action or deliverable is requested without guessing.

- **Strong:** concrete verbs, named artifacts, clear scope in the first prompt.
- **Weak:** vague imperatives (“fix it”, “make it better”), pronouns without referents, multiple possible interpretations.

### 2. Context & motivation

Why constraints exist when it matters — background, stack, prior decisions, or user goal that shapes the right answer.

- **Strong:** relevant file paths, error messages, constraints tied to a goal.
- **Weak:** task stated with no situational context when context would change the approach.

### 3. Success criteria

What “done” means — observable outcomes, acceptance checks, or explicit definition of correct behavior.

- **Strong:** “passes these tests”, “matches this API shape”, “user can log in with magic link”.
- **Weak:** no way to verify completion; open-ended “just make it work” without a finish line.

### 4. Structure

Steps when order matters; instructions separated from data; readable layout for multi-part asks.

- **Strong:** numbered steps, labeled sections, pasted code/logs separated from instructions.
- **Weak:** wall of text mixing requirements and raw dumps; critical ordering left implicit.

### 5. Constraints & boundaries

Scope, must/must-not, safety/agentic limits — what to touch, what to avoid, time/scope bounds.

- **Strong:** “only change `auth.ts`”, “do not commit”, “no new dependencies”.
- **Weak:** unbounded “refactor everything” or missing guardrails on risky operations.

### 6. Examples (when format/judgment matters)

Reference examples when output format, style, or judgment consistency matters.

- **Strong:** sample input/output, prior art, or “like X but with Y”.
- **Weak:** format-sensitive request with no exemplar when ambiguity is high.
- **N/A:** when the task is fully specified without format ambiguity.

### 7. Agentic hygiene

Proportionate scope; avoid over-eager or test-gaming instructions; state boundaries for long runs.

- **Strong:** right-sized tasks, honest constraints, no “ignore tests” or “ship at all costs”.
- **Weak:** contradictory autonomy (“do everything” + “don’t change anything”), gaming evals, unbounded agent loops without checkpoints.

### 8. Cross-session consistency

Stable constraints and style across the sample; flag contradictory habits without reason.

- **Strong:** similar tasks get similar level of detail and constraints.
- **Weak:** same project/context treated inconsistently (detailed specs in one session, one-liners in the next) without explanation.

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

## Decision order

Apply in this order; do not skip steps.

1. **Checklist** — Score applicable dimensions on the dossier; identify primary gap themes with evidence.
2. **Consistency** — Assess cross-session contradictions; note and possibly cap the letter when contradictory habits appear without reason.
3. **Signal modifiers** — Apply lightly per `signals.md` (may pull down one letter only when corroborated by craft gaps).
4. **Emit one letter** — Single overall A–D plus structured feedback.

## Never inflate

Polish, politeness, or length do **not** raise a grade built on chronic under-specification. A verbose but vague sample remains weak. Grade on craft and efficacy, not eloquence.
