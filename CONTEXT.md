# Grader

Glossary for the prompt-grading product. Implementation details do not belong here.

## Language

**Craft**:
The D1–D11 rubric axis for a single composed prompt: band, caveated percent, confidence, dimension levels, caps, and rationales.
_Avoid_: Skill score, DNA, overall grade (when meaning only this axis)

**Efficacy**:
The outcome axis for attributed rework and related session metrics (restates, corrections, rates), plus a short attribution narrative. Not a letter grade.
_Avoid_: Efficiency (v2 letter), rework score

**Planning**:
The outcome axis of scope-change counters and signal callouts (`under_specified_initial_plan`, `planned_decomposition`, and kin). Not a letter grade.
_Avoid_: Planning score (letter), plan grade

**Grade report**:
The learner-facing, fixed-section rendering of Craft, Efficacy, Planning, security, and coaching slots from finalized data.
_Avoid_: Profile, Prompting Profile, verdict sheet

**Tri-pane cockpit**:
The canonical grade-report layout: topbar (Craft headline + Security), three panes (Craft | Efficacy | Planning), dimension chips with rationales in details, coaching slots along the bottom. Markdown uses the same regions in a fixed linear section order.
_Avoid_: Linear dossier, Focus rail, Prompting Profile

**Session rollup**:
A grade report that reuses the Tri-pane cockpit shell across many prompts in one intake window (intake topbar, aggregate panes, exemplars in coaching slots).
_Avoid_: Dossier (unless meaning legacy export intake), profile summary, mix-table-only rollup
