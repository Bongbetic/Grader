from pathlib import Path

SHEET = Path(__file__).resolve().parents[1] / "skills" / "grader" / "references" / "rubric-sheet.md"


def test_sheet_covers_classification_and_attribution():
    text = SHEET.read_text(encoding="utf-8").lower()
    for needle in [
        "task complexity",
        "prompt_class",
        "task_complexity",
        "rework_cause",
        "user_under_specified",
        "evidence span",
        "abstain",
        "workflow_protocol_reply",
        "required",
    ]:
        assert needle in text, f"missing guidance: {needle}"
