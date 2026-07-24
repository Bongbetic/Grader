from pathlib import Path

SHEET = Path(__file__).resolve().parents[1] / "skills" / "grader" / "references" / "rubric-sheet.md"


def test_sheet_has_proportionality_and_conventions():
    text = SHEET.read_text(encoding="utf-8").lower()
    for needle in [
        "foreseeable need",
        "proportional",
        "underinvested_for_task",
        "valid_continuation",
        "d2",
        "divergence",
        "reasoning model",
        "delimiters",
    ]:
        assert needle in text, f"missing: {needle}"
