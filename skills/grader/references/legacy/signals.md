# Conversation efficacy signals

Light **modifiers** to the checklist-based Skill letter. Signals come from dossier `signals` fields (per session) and conversation patterns in `user_prompts[]`.

Signals corroborate or slightly adjust the Skill letter already implied by checklist craft. Conversation efficacy is also reported under the separate Efficiency score; Efficiency does not prove craft quality by itself.

## Allowed signals

Use these when present in the dossier or evident from the transcript sample:

| Signal | Meaning | Dossier field |
|--------|---------|---------------|
| **Corrections** | User corrects the same misunderstanding — “no, wrong”, “not what I meant”, “actually,”, “fix:”, “that’s incorrect” | `signals.corrections` |
| **Restates** | User repeats the same ask with little new information (high token overlap, similar length) | `signals.restates` |
| **Clarify loops** | Assistant asks clarifying questions; user replies remain vague; pattern repeats | `signals.clarify_loops` |
| **Abandoned goals** | Task dropped mid-thread without resolution — cancel/abort language or abrupt short final prompt after a long thread | `signals.abandoned_goal` |

## Allowed efficacy signals

Report prompts-per-task, single-shot completion, and rework rates as **conversation efficacy** under the separate Efficiency score. These signals can describe whether the conversation reached outcomes with fewer clarification/correction cycles, but they are never proof of good prompting craft alone.

### How to use modifiers

- Apply **after** checklist scoring and consistency assessment (see `checklist.md` decision order).
- A signal modifier may pull the letter down **at most one step** (A→B, B→C, C→D) when the signal is **strong and corroborated by craft gaps** (e.g. vague prompts *and* heavy correction loops).
- Multiple weak signals do not stack beyond one letter step.
- Signals alone **must not** invent a **D**. A D requires foundational checklist gaps (habitual under-specification, contradictions, or dominant craft failures), not conversation friction on otherwise strong prompts.

## Forbidden metrics

Do **not** use as grading inputs or report fields:

- Token counts or context-window usage
- Cost, spend, burn, or pricing narratives
- Cache hit rates or latency
- Model-tier comparisons framed as “efficiency”
- Any metric that rewards brevity or punishes length without craft evidence

Forbidden efficiency framing includes token/cost/latency/cache narratives, model-tier “efficiency,” and any metric that rewards brevity without craft evidence. If the user asks about cost/tokens, redirect: this grader assesses **prompting craft and conversation efficacy**, not resource usage.

## Relationship to checklist

| Checklist craft | Signals | Typical outcome |
|-----------------|---------|-----------------|
| Strong | Low | Hold letter (A or B) |
| Strong | High | Note friction; usually no downgrade unless pattern is severe and unexplained |
| Weak | Low | C from craft; signals do not deepen further |
| Weak | High | C or one-step downgrade (e.g. B→C, C→D) when signals corroborate craft gaps |

When in doubt, favor checklist evidence over signals.

## Relationship to Efficiency

Efficiency is a separate axis from Skill. Prompts-per-task, single-shot, and rework-rate evidence may support the Efficiency score and may lightly modify Skill only under the rules above; token, cost, latency, cache, and model-tier measures remain disallowed.
