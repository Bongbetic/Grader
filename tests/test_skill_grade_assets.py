"""Asset tests for the v3 Grade skill markdown and rubric references."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "grader" / "SKILL.md"
GRADE_FLOW = ROOT / "skills" / "grader" / "flows" / "grade.md"
RUBRIC_SHEET = ROOT / "skills" / "grader" / "references" / "rubric-sheet.md"
JUDGE_CONSISTENCY = ROOT / "skills" / "grader" / "references" / "judge-consistency.md"


@pytest.fixture
def skill_text():
    return SKILL.read_text(encoding="utf-8")


@pytest.fixture
def grade_flow_text():
    return GRADE_FLOW.read_text(encoding="utf-8")


@pytest.fixture
def rubric_text():
    return RUBRIC_SHEET.read_text(encoding="utf-8")


def test_skill_md_exists_and_references_v3_rubric(skill_text):
    assert SKILL.is_file()
    for dim in [f"D{i}" for i in range(1, 12)]:
        assert dim in skill_text, f"SKILL.md missing {dim}"
    assert "finalize_grade" in skill_text
    assert "scan_intake" in skill_text
    assert "consent" in skill_text
    assert "rubric-sheet" in skill_text
    assert "judge-schema" in skill_text
    assert "judge-consistency" in skill_text


def test_judge_consistency_policy_doc_exists():
    assert JUDGE_CONSISTENCY.is_file()
    text = JUDGE_CONSISTENCY.read_text(encoding="utf-8")
    assert "model agnostic" in text.lower()
    assert "deterministic" in text.lower()
    assert "host-LLM judge JSON" in text
    assert "heuristic" in text.lower()
    assert "target_model_class" in text
    assert "cross-class" in text.lower() or "cross class" in text.lower()
    assert "scale playbook" in text.lower() or "flows/grade.md" in text


def test_skill_md_forbids_heuristic_batch_judge(skill_text):
    assert "host-LLM judge JSON per prompt" in skill_text
    assert "heuristic batch" in skill_text.lower() or "no heuristic" in skill_text.lower()


def test_grade_flow_links_judge_consistency_policy(grade_flow_text):
    assert "judge-consistency" in grade_flow_text


def test_skill_md_you_are_the_judge(skill_text):
    assert "You are the judge" in skill_text
    assert "install_skill" in skill_text


def test_skill_md_lists_four_flows(skill_text):
    for flow in ["grade.md", "coach.md", "practice.md", "trends.md"]:
        assert f"flows/{flow}" in skill_text


def test_skill_md_forbids_token_cost_metrics(skill_text):
    assert "No token/cost metrics" in skill_text or "no token/cost metrics" in skill_text.lower()


def test_grade_flow_references_judge_schema_and_clis(grade_flow_text):
    assert GRADE_FLOW.is_file()
    assert "judge-schema" in grade_flow_text
    assert "scan_intake.py" in grade_flow_text
    assert "finalize_grade.py" in grade_flow_text
    assert "consent" in grade_flow_text
    assert "DISQUALIFIER_IDS" in grade_flow_text
    assert "model_class.classify" in grade_flow_text
    assert "AS-005" in grade_flow_text
    assert "D5 excluded from the score denominator" in grade_flow_text
    assert "capped at level 1" not in grade_flow_text


def test_d5_unknown_docs_match_score_math(rubric_text, skill_text, grade_flow_text):
    """Docs must follow score_math: unknown class excludes D5, never min(level, 1)."""
    combined = rubric_text + skill_text + grade_flow_text
    assert "min(level, 1)" not in combined
    assert "exclude" in rubric_text.lower() and "D5" in rubric_text
    assert "AS-005" in skill_text or "excludes D5" in skill_text


def test_grade_flow_branches_proceed_summary(grade_flow_text):
    assert "scan path" in grade_flow_text.lower()
    assert "paste/import path" in grade_flow_text.lower()
    assert "redaction_flags" in grade_flow_text


def test_skill_md_privacy_hard_gate(skill_text):
    assert "upload transcripts to third parties" in skill_text


def test_grade_flow_has_judge_instructions(grade_flow_text):
    assert "you are the judge" in grade_flow_text.lower()
    assert "return only schema json" in grade_flow_text.lower()
    assert "N/A" in grade_flow_text
    assert "conditional" in grade_flow_text.lower()
    assert "classification" in grade_flow_text.lower()
    assert "task_complexity" in grade_flow_text
    assert "prompt_class" in grade_flow_text
    assert "proportionality" in grade_flow_text.lower()
    assert "valid_continuation" in grade_flow_text


def test_grade_flow_asks_model_class_when_unknown(grade_flow_text):
    assert "unknown" in grade_flow_text.lower()
    assert "ask the learner" in grade_flow_text.lower()
    assert "target_model_class" in grade_flow_text


def test_grade_flow_renderer_only_playbook(grade_flow_text):
    """Host must judge → finalize → enrich/slots → render; never freestyle narrate."""
    lower = grade_flow_text.lower()
    assert "do not freestyle-narrate the grade" in lower
    assert "render_grade_md.py" in grade_flow_text
    assert "render_grade_html.py" in grade_flow_text
    assert "--efficacy-json" in grade_flow_text
    assert "--planning-json" in grade_flow_text
    assert "build_session_outcome" in grade_flow_text
    assert "slots" in lower
    assert "<=120" in grade_flow_text
    assert "<=80" in grade_flow_text
    assert "tri-pane cockpit" in lower or "tri-pane" in lower
    # Old freestyle summary bullets must not return
    assert "letter + percent" not in lower
    assert "one-line rationale" not in lower


def test_rubric_sheet_exists_and_covers_rubric(rubric_text):
    assert RUBRIC_SHEET.is_file()
    for dim in [f"D{i}" for i in range(1, 12)]:
        assert dim in rubric_text, f"rubric-sheet missing {dim}"
    assert "Scoring procedure" in rubric_text
    assert "Grade bands" in rubric_text or "Grade band" in rubric_text
    assert "Disqualifier" in rubric_text
    assert "Teaching layer" in rubric_text
    assert "fair-terse-valid-continuation" in rubric_text
    assert "adv-fake-criteria" in rubric_text
    assert "adv-contradictory" in rubric_text
    assert "judge-consistency" in rubric_text


def test_v2_grade_sources_retired_from_skill_root():
    assert not (ROOT / "skills" / "grader" / "checklist.md").exists()
    assert not (ROOT / "skills" / "grader" / "signals.md").exists()


def test_skill_md_documents_windows_shell_and_cursor_import(skill_text):
    assert "PowerShell 5.1" in skill_text
    assert "PowerShell 7" in skill_text
    assert "grader-import" in skill_text


def test_grade_flow_documents_windows_shell_and_cursor_import(grade_flow_text):
    assert "PowerShell 5.1" in grade_flow_text
    assert "PowerShell 7" in grade_flow_text
    assert "grader-import" in grade_flow_text
