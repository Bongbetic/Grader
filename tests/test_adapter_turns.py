import adapters.claude as claude_adapter


def test_discover_turns_yields_indexed_session_turns(monkeypatch):
    fake_session = {
        "started_at": "2026-07-24T00:00:00Z",
        "user_prompts": ["first prompt", "second prompt"],
    }
    monkeypatch.setattr(claude_adapter.consent, "has_consent", lambda tool: True)
    monkeypatch.setattr(claude_adapter.allowlist, "paths_for_tool", lambda tool: ["/fake/s1.jsonl"])
    monkeypatch.setattr(
        claude_adapter.grader_lib, "select_recent_sessions", lambda paths, limit: paths
    )
    monkeypatch.setattr(
        claude_adapter.grader_lib, "parse_session_jsonl", lambda path: fake_session
    )

    turns = claude_adapter.discover_turns(limit=10)
    assert [t["turn_index"] for t in turns] == [0, 1]
    assert all(t["role"] == "user" for t in turns)
    assert turns[0]["session_id"] == turns[1]["session_id"]
    assert turns[0]["session_id"]  # non-empty
