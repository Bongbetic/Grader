from __future__ import annotations

from domain import GradeReport, NA

TEACHING_FIXES: dict[str, str] = {
    "D1": "What does a perfect result look like, and how would you check it? Add a one-line acceptance test.",
    "D2": "State the audience and why you need this; the 'why' lets the model resolve edge cases you didn't foresee.",
    "D3": "Add scope boundaries and one length/format constraint; then scan for any two instructions that fight each other.",
    "D4": "Show the shape you want (a two-line skeleton or JSON stub) instead of describing it; separate your instructions from your data.",
    "D5": "Decide the model class first. Standard model + hard task → add reasoning scaffolding. Reasoning model → strip CoT and examples, set the effort level.",
    "D6": "Cut every sentence that doesn't change the output. Read it as a stranger would.",
    "D7": "Write the pass/fail check before running; change one thing at a time when iterating.",
    "D8": "Paste the source material (scoped, not dumped) rather than trusting recall; ask for citations.",
    "D9": "Add one aligned example; only add a second if output still drifts; keep example format identical.",
    "D10": "Name style, tone, and audience separately (CO-STAR's insight); avoid caricature personas.",
    "D11": "Add 'If you're unsure or the data is insufficient, say so rather than guessing,' plus a verification step for high-stakes output.",
}


def coaching_notes(report: GradeReport) -> list[dict]:
    """Return one coaching note per dimension with level < 3."""
    notes: list[dict] = []
    for score in report.dimension_scores:
        if score.level == NA:
            continue
        if isinstance(score.level, int) and score.level < 3:
            notes.append(
                {
                    "dimension_id": score.dimension_id,
                    "fix_text": TEACHING_FIXES[score.dimension_id],
                    "lesson_ref": score.dimension_id,
                }
            )
    return notes
