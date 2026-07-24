from pathlib import Path

FLOW = Path(__file__).resolve().parents[1] / "skills" / "grader" / "flows" / "grade.md"


def test_grade_flow_documents_three_axes_and_omission():
    text = FLOW.read_text(encoding="utf-8").lower()
    for needle in ["craft", "efficacy", "planning", "confidence", "workflow_protocol_reply"]:
        assert needle in text, f"missing: {needle}"
    assert "render_grade_md.py" in FLOW.read_text(encoding="utf-8")
    assert "do not freestyle-narrate" in text
