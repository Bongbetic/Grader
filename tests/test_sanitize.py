import pytest

import sanitize


@pytest.mark.parametrize(
    ("raw", "expected", "note"),
    [
        (
            "<user_query>fix the login bug</user_query>",
            "fix the login bug",
            "stripped_user_query_tags",
        ),
        (
            (
                "<manually_attached_skills>\n"
                "Skill Name: implement\n"
                "SKILL.md content here\n"
                "</manually_attached_skills>\n"
                "<user_query>/implement #16</user_query>"
            ),
            "/implement #16",
            "stripped_user_query_tags",
        ),
        (
            (
                "<mcp_meta_tools>\n"
                "Available MCP servers: cursor-ide-browser\n"
                "</mcp_meta_tools>\n"
                "<user_query>run the tests</user_query>"
            ),
            "run the tests",
            "stripped_user_query_tags",
        ),
        (
            (
                "<hook_context>\n"
                "pre-commit hook blocked commit\n"
                "</hook_context>\n"
                "<user_query>commit anyway</user_query>"
            ),
            "commit anyway",
            "stripped_user_query_tags",
        ),
        (
            (
                "You have access to MCP tools through GetMcpTools.\n\n"
                "add pagination to the API"
            ),
            "add pagination to the API",
            "stripped_preamble",
        ),
        (
            (
                "<subagent>\n"
                "Dispatch generalPurpose agent to explore codebase.\n"
                "</subagent>\n"
                "<user_query>review the diff</user_query>"
            ),
            "review the diff",
            "stripped_user_query_tags",
        ),
        (
            "plain learner prompt with no tags",
            "plain learner prompt with no tags",
            None,
        ),
    ],
)
def test_sanitize_learner_text(raw, expected, note):
    cleaned, notes = sanitize.sanitize_learner_text(raw)
    assert cleaned == expected
    if note:
        assert note in notes


def test_sanitize_empty_and_whitespace():
    assert sanitize.sanitize_learner_text("") == ("", [])
    assert sanitize.sanitize_learner_text("   ") == ("   ", [])


def test_sanitize_strips_git_status_without_user_query():
    raw = (
        "<git_status>\n"
        "?? observed-shortcomings.md\n"
        "</git_status>\n"
        "ship the sanitizer"
    )
    cleaned, notes = sanitize.sanitize_learner_text(raw)
    assert cleaned == "ship the sanitizer"
    assert "stripped_boilerplate_block" in notes
