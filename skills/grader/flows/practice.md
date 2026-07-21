# Practice flow

Use this flow when the user asks to practice prompting, wants exercises, wants drills, or asks for feedback on practice answers. Practice is training only; it does not create coach history credit.

## 1. Build or refresh the baseline

From this skill directory, run the shared dig when host filesystem access is available:

```bash
python scripts/extract_dossier.py --limit 100 --prompt-limit 100
```

If local dig is unavailable, ask for `/export`, pasted prompts, or a few representative prompts. For an export file:

```bash
python scripts/extract_dossier.py --export /path/to/export.md
```

Read `checklist.md` and `signals.md`, then identify the weakest applicable DNA dimensions. Do not use forbidden token/cost/latency/cache metrics.

## 2. Choose practice targets

Pick 1-3 target dimensions from the weakest patterns, usually among:

- `clarity`
- `context`
- `success_criteria`
- `structure`
- `constraints`
- `examples`
- `agentic_hygiene`
- `cross_session_consistency`

Explain the targets in one short paragraph. If there is no history, ask the user what kind of agent work they usually delegate and select targets from that context.

## 3. Generate exercises

Create 5-10 exercises. Keep them realistic and varied:

- At least two small scoped implementation prompts.
- At least one debugging or log-triage prompt.
- At least one review/planning prompt.
- At least one prompt where constraints and non-goals matter.

For each exercise, include:

1. Scenario.
2. User goal.
3. Hidden grading focus, stated plainly enough that the user knows what to practice.
4. Optional hints only after the user attempts the exercise.

Do not reveal a perfect answer immediately unless the user asks.

## 4. Optional grade-replies loop

If the user answers exercises, grade each reply briefly:

- A-D practice score for that exercise.
- What worked.
- What was missing.
- One stronger rewrite.
- One next micro-drill.

This exercise score is local practice feedback, not the official historical overall grade. Keep evidence grounded in the user's practice answer and the checklist.

## 5. History rule

Do not append coach history. Practice flow gives no trends credit, even if the user completes many exercises. If the user wants trends credit, offer to start a Coach flow with the four-task live assessment and at least one coaching drill round.
