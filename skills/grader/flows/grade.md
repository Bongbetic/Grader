# Grade flow

Use this flow for the default `/grader` intent: grade one or more prompts against the v3 rubric and produce a `GradeReport` for each.

## 1. Gather consent and run intake

Before reading any local tool history, confirm the user has granted per-tool consent. Grant consent from this skill directory with:

```bash
python3 scripts/grant_consent.py --tool claude
```

Or call `consent.grant_consent(tool)` from `scripts/consent.py`. Then run the allowlisted scan:

```bash
python3 scripts/scan_intake.py --tools claude --json
```

For server-side tools or pasted prompts, use the import/paste adapter instead:

```python
import sys
sys.path.insert(0, "scripts")
from adapters import import_paste

candidates = import_paste.from_text(pasted_text, source="paste")
```

Each candidate becomes a `PromptRecord` through `scripts/normalize.py`, which redacts secrets and emails before any further step.

## 2. Present intake summary and ask to proceed

Both scan and paste/import paths require explicit Learner confirmation before grading. If the user declines, stop and do not judge any prompt.

**Scan path:** show the JSON summary from `scan_intake.py` (tool, candidate count, time range, redaction count).

**Paste/import path:** after `normalize.to_prompt_record`, present a short summary:

- **Source:** `import` or `paste` (from `PromptRecord.source_tool`)
- **Count:** number of prompt records
- **Redaction notes:** summarize `PromptRecord.redaction_flags` (secrets or emails detected by `scripts/redact.py`)

Grade only after the Learner confirms.

## 3. Judge each prompt

**You are the judge.** The agent running this skill scores each prompt — there is no external judge service.

Omit any turn classified `workflow_protocol_reply` from Craft grading and from efficacy rework counts. Grade only turns where the user composes their own instruction.

For each prompt record:

1. Read `references/rubric-sheet.md` and `references/judge-schema.json`.
2. Score the full redacted prompt (`PromptRecord.redacted_text`) against D1-D11 yourself:
   - Return only schema JSON from `references/judge-schema.json` — no markdown, no preamble, no explanation outside the JSON.
   - Mark conditional dimensions (D8-D11) **N/A** when the task does not trigger them.
   - Set a `disqualifiers` array with exact IDs from `DISQUALIFIER_IDS` in `scripts/domain.py` when any cap applies.
3. Write the JSON object to a temp file or pass it directly to `finalize_grade.py`.

Example judge JSON shape:

```json
{
  "dimensions": {
    "D1": {"level": 3, "rationale": "Clear action and acceptance criteria."},
    "D2": {"level": 2, "rationale": "Background present; motivation implied."},
    "D8": {"level": "N/A", "rationale": "No factual grounding needed."}
  },
  "disqualifiers": []
}
```

## 4. Resolve model class and finalize

Before `finalize_grade.py`, resolve `--model-class` for each prompt:

1. Read `target_model_class` from the `PromptRecord` (set by `model_class.classify(model_hint)` during normalize).
2. If `unknown`, ask the Learner which model class the prompt targeted (`standard` or `reasoning`). If they skip or cannot say, keep `unknown` (AS-005: D5 excluded from the score denominator; `wrong_model_class` cap suppressed).
3. To re-classify from a model hint, use `scripts/model_class.py`:

```python
import model_class
model_class.classify("gpt-4o")  # "standard"
model_class.classify("o1-preview")  # "reasoning"
model_class.classify(None)  # "unknown"
```

When session context exists for this prompt, build Efficacy and Planning JSON (report-shaped fields from [Wire efficacy planning and outcome modifier into finalize](https://github.com/Bongbetic/Grader/issues/9)) and pass both. When either is missing, omit that flag — finalize marks the axis `unavailable` with `no session context`.

For **claude**, **cursor**, or **codex** intake, derive both JSON objects from segmented turns via `discover_turns` (not a cursor-only branch):

```bash
python3 scripts/build_session_outcome.py \
  --tool <claude|cursor|codex> \
  [--session-id <session-id>] \
  [--home path/to/tool/home] \
  --efficacy-out path/to/efficacy.json \
  --planning-out path/to/planning.json
```

Or from Python:

```python
import sys
sys.path.insert(0, "scripts")
from build_session_outcome import build_session_outcome

efficacy, planning = build_session_outcome(
    "cursor",
    session_id="<session-id>",
    follow_up_labels={},          # host judge labels when available
    scope_change_labels=[],       # host judge labels when available
    consent_covers_transcript=True,
)
```

`tool_or_environment` attribution confidence is capped at **medium** when the adapter cannot preserve tool outputs (Cursor today). Merge host `follow_up_labels` / `scope_change_labels` before calling; the builder applies the cap and sets `high_confidence_user_underspec` / `high_confidence_underspec` for finalize.

Run the deterministic finalizer for each judge output:

```bash
python3 scripts/finalize_grade.py \
  --judge path/to/judge.json \
  --prompt-id <record-id> \
  --excerpt "<redacted excerpt>" \
  [--raw path/to/raw.txt] \
  [--persist-raw] \
  --model-class <standard|reasoning|unknown> \
  [--efficacy-json path/to/efficacy.json] \
  [--planning-json path/to/planning.json] \
  [--mean-kappa <float>]
```

`finalize_grade.py` validates the judge JSON, recomputes earned/possible/percent/band/caps, attaches Efficacy / Planning (+ optional outcome modifier), persists under `~/.grader/`, and prints the finalized report JSON to stdout.

**Do not freestyle-narrate the grade.** Never invent your own letter/percent/dimension/axis summary for the Learner. The deterministic renderer owns Craft, Efficacy, Planning, Dimensions, and Security layout.

## 5. Enrich report JSON, fill hybrid slots, render

Save finalize stdout to a temp report file. Before rendering, merge these optional fields onto that JSON object (finalize does not emit them all):

| Field | Source | Notes |
|-------|--------|-------|
| `excerpt` | redacted prompt excerpt | Required for Craft pane |
| `security` | from `PromptRecord.redaction_flags` / residual hits | Omit or `{status: "none"}` when clear → renderer shows `none detected` |
| `classification_summary` | session classification when available | Drives template-first Efficacy attribution (`rework_cause`) |
| `slots` | hybrid coaching fills (this step) | See caps below |

### Hybrid slots (host fills; renderer hard-truncates)

Write `slots` before the first render (preferred) or after a placeholder render, then re-render:

- `strongest` — <=120 chars: what worked in this prompt
- `weakest` — <=120 chars: recurring leak to fix
- `next_actions` — <=3 bullets, each <=80 chars: concrete next practices

Do not invent extra coaching sections. Do not rewrite Craft / Efficacy / Planning prose — attribution and callouts come from the renderer templates.

### Render (required)

Default to markdown. Use HTML when the Learner asks for HTML or a browser surface:

```bash
python3 scripts/render_grade_md.py --report path/to/report.json
```

```bash
python3 scripts/render_grade_html.py --report path/to/report.json
```

Show the renderer stdout to the Learner **unchanged** — fixed Tri-pane cockpit twin (Topbar → Craft → Efficacy → Planning → Dimensions → Security → Coaching). No freestyle headings, no parallel “summary” block beside it.

Three axes always appear via the renderer: **Craft** (band raw→adjusted, caveated %, confidence, modifier), **Efficacy**, **Planning**. Outcome modifier reason appears only when finalize set it; band drops at most one letter on high-confidence, user-attributable evidence.

### Session rollup (multi-prompt intake)

When the Learner graded **more than one** prompt in this intake window and wants a session view, compose after per-prompt renders (or instead of repeating every prompt):

```bash
python3 scripts/compose_session_rollup.py \
  --reports path/to/p1.json path/to/p2.json \
  [--intake-json path/to/intake.json] \
  [--session-id <id>]
```

Stdout is shared-schema JSON (`grain=session_rollup`). Fill `slots.next_actions` (host hybrid; strongest/weakest already exemplar-seeded), then render with the same markdown/HTML CLIs. Do not freestyle a rollup narrative.

## 6. Offer practice or coach

After grading, offer the user a choice:

- Run `flows/practice.md` on the weakest scored dimension.
- Run `flows/coach.md` for a deeper rewrite session.
- Exit the Grade flow.

Do not append coach history in the Grade flow. History credit is only for completed Coach sessions.
