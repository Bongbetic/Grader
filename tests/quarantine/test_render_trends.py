import re

from history_lib import append_coach_session
from render_trends import build_trends_payload, main, render_trends_html


def _complete(i, root):
    append_coach_session(
        {
            "id": str(i),
            "completed_at": f"2026-07-{i:02d}T00:00:00Z",
            "completed": True,
            "live_assessment_finished": True,
            "coaching_drill_rounds": 1,
            "dna_scores": {"clarity": 3 + i, "constraints": 2 + i},
            "scores": {"skill": "B", "efficiency": "C", "consistency": "B"},
            "habits_focus": ["constraints"],
            "live_assessment_summary": {},
            "notes": "",
        },
        claude_root=root,
    )


def test_trends_html_denies_under_five(tmp_path):
    for i in range(1, 5):
        _complete(i, tmp_path)
    payload = build_trends_payload(tmp_path)
    html = render_trends_html(payload)
    assert payload["status"]["unlocked"] is False
    assert "4/5" in html or "4 of 5" in html
    assert "trends unlocked" not in html.lower()
    assert "coach" in html.lower()
    assert not re.search(r"""\ssrc\s*=\s*['\"]https?://""", html, re.I)
    assert "https://" not in html


def test_trends_html_charts_when_unlocked(tmp_path):
    for i in range(1, 6):
        _complete(i, tmp_path)
    html = render_trends_html(build_trends_payload(tmp_path))
    assert "<svg" in html.lower()
    assert "https://" not in html
    assert "Prompt" in html or "Trend" in html


def test_trends_payload_filters_to_completions_when_unlocked(tmp_path):
    for i in range(1, 6):
        _complete(i, tmp_path)
    append_coach_session(
        {
            "id": "incomplete",
            "completed_at": "2026-07-06T00:00:00Z",
            "completed": False,
            "live_assessment_finished": False,
            "coaching_drill_rounds": 0,
        },
        claude_root=tmp_path,
    )

    payload = build_trends_payload(tmp_path)

    assert payload["status"]["unlocked"] is True
    assert [session["id"] for session in payload["sessions"]] == ["1", "2", "3", "4", "5"]


def test_trends_cli_writes_locked_html_and_exits_zero(tmp_path):
    for i in range(1, 5):
        _complete(i, tmp_path)
    out = tmp_path / "trends.html"

    assert main(["--root", str(tmp_path), "--out", str(out)]) == 0

    html = out.read_text(encoding="utf-8")
    assert "4/5" in html
    assert "<svg" not in html.lower()
    assert "http://" not in html
    assert "https://" not in html
