import json
import re
from pathlib import Path

from render_report import main, render_profile_html

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "grader"
    / "fixtures"
    / "profiles"
    / "sample_grade_profile.json"
)


def test_render_profile_html_is_self_contained_and_shows_dna():
    profile = json.loads(FIXTURE.read_text(encoding="utf-8"))
    html = render_profile_html(profile)
    assert "Your Prompting Profile" in html
    assert "Prompt DNA" in html or "DNA" in html
    assert "Skill" in html and "Efficiency" in html
    assert not re.search(r"""\ssrc\s*=\s*['\"]https?://""", html, re.I)
    assert "https://" not in html and "http://" not in html
    assert "<style" in html


def test_render_profile_html_escapes_user_strings():
    profile = json.loads(FIXTURE.read_text(encoding="utf-8"))
    profile["habits"] = ["Use <script>alert('x')</script> in a prompt"]
    profile["learning_cards"][0]["title"] = "Clarify & verify"
    profile["dna"][0]["evidence"] = ["acceptance <criteria>"]
    html = render_profile_html(profile)
    assert "<script>alert('x')</script>" not in html
    assert "Use &lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt; in a prompt" in html
    assert "Clarify &amp; verify" in html
    assert "acceptance &lt;criteria&gt;" in html


def test_cli_writes_report_html(tmp_path):
    out = tmp_path / "report.html"
    rc = main(["--in", str(FIXTURE), "--out", str(out)])
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    assert "Your Prompting Profile" in html
    assert "<style" in html
