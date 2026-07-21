# Conversation efficacy signals

Light **modifiers** to the checklist-based grade. Signals come from dossier `signals` fields (per session) and conversation patterns in `user_prompts[]`.

Signals are **not** a separate score. They corroborate or slightly adjust a letter already implied by checklist craft.

## Allowed signals

Use these when present in the dossier or evident from the transcript sample:

| Signal | Meaning | Dossier field |
|--------|---------|---------------|
| **Corrections** | User corrects the same misunderstanding — “no, wrong”, “not what I meant”, “actually,”, “fix:”, “that’s incorrect” | `signals.corrections` |
| **Restates** | User repeats the same ask with little new information (high token overlap, similar length) | `signals.restates` |
| **Clarify loops** | Assistant asks clarifying questions; user replies remain vague; pattern repeats | `signals.clarify_loops` |
| **Abandoned goals** | Task dropped mid-thread without resolution — cancel/abort language or abrupt short final prompt after a long thread | `signals.abandoned_goal` |

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

If the user asks about cost/tokens, redirect: this grader assesses **prompting craft and conversation efficacy**, not resource usage.

## Relationship to checklist

| Checklist craft | Signals | Typical outcome |
|-----------------|---------|-----------------|
| Strong | Low | Hold letter (A or B) |
| Strong | High | Note friction; usually no downgrade unless pattern is severe and unexplained |
| Weak | Low | C from craft; signals do not deepen further |
| Weak | High | C or one-step downgrade (e.g. B→C, C→D) when signals corroborate craft gaps |

When in doubt, favor checklist evidence over signals.
