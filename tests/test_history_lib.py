from history_lib import (
    TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS,
    append_coach_session,
    count_completed_coach_sessions,
    is_coach_completion,
    load_coach_sessions,
    trends_unlock_status,
)


def test_incomplete_coach_does_not_count(tmp_path):
    root = tmp_path
    append_coach_session({
        "id": "1",
        "completed_at": "2026-07-01T00:00:00Z",
        "completed": False,
        "live_assessment_finished": False,
        "coaching_drill_rounds": 0,
        "dna_scores": {},
        "scores": {"skill": "B", "efficiency": "C", "consistency": "B"},
        "habits_focus": [],
        "live_assessment_summary": {},
        "notes": "",
    }, claude_root=root)
    assert count_completed_coach_sessions(load_coach_sessions(root)) == 0
    status = trends_unlock_status(root)
    assert status["unlocked"] is False
    assert status["completed"] == 0
    assert status["required"] == 5
    assert status["remaining"] == 5


def test_trends_unlocks_at_five_completed(tmp_path):
    assert TRENDS_UNLOCK_COMPLETED_COACH_SESSIONS == 5
    root = tmp_path
    for i in range(4):
        append_coach_session({
            "id": str(i),
            "completed_at": f"2026-07-0{i+1}T00:00:00Z",
            "completed": True,
            "live_assessment_finished": True,
            "coaching_drill_rounds": 1,
            "dna_scores": {"clarity": 5},
            "scores": {"skill": "B", "efficiency": "B", "consistency": "B"},
            "habits_focus": ["constraints"],
            "live_assessment_summary": {"tasks": 4},
            "notes": "",
        }, claude_root=root)
    assert trends_unlock_status(root)["unlocked"] is False
    assert trends_unlock_status(root)["remaining"] == 1
    append_coach_session({
        "id": "5",
        "completed_at": "2026-07-05T00:00:00Z",
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 2,
        "dna_scores": {"clarity": 7},
        "scores": {"skill": "A", "efficiency": "B", "consistency": "A"},
        "habits_focus": ["constraints"],
        "live_assessment_summary": {"tasks": 4},
        "notes": "improved",
    }, claude_root=root)
    status = trends_unlock_status(root)
    assert status["unlocked"] is True
    assert status["completed"] == 5
    assert status["remaining"] == 0


def test_is_coach_completion_requires_drill_round():
    assert is_coach_completion({
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 1,
    })
    assert not is_coach_completion({
        "completed": True,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 0,
    })
    assert not is_coach_completion({
        "completed": 1,
        "live_assessment_finished": True,
        "coaching_drill_rounds": 1,
    })
    assert not is_coach_completion({
        "completed": "yes",
        "live_assessment_finished": True,
        "coaching_drill_rounds": 1,
    })
    assert not is_coach_completion({
        "completed": True,
        "live_assessment_finished": 1,
        "coaching_drill_rounds": 1,
    })
