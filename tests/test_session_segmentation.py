from grader_lib import segment_tasks_by_session


def test_tasks_never_span_sessions():
    sessions = [
        {"session_id": "s1", "user_prompts": ["build a parser", "add tests for it"]},
        {"session_id": "s2", "user_prompts": ["refactor the parser module"]},
    ]
    tasks = segment_tasks_by_session(sessions)
    assert all("session_id" in t for t in tasks)
    session_ids = {t["session_id"] for t in tasks}
    assert session_ids == {"s1", "s2"}
    # s2's single prompt is its own task, never merged with s1
    s2_tasks = [t for t in tasks if t["session_id"] == "s2"]
    assert len(s2_tasks) == 1


def test_empty_sessions_yield_no_tasks():
    assert segment_tasks_by_session([]) == []
