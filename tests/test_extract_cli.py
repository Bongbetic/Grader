import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "grader" / "scripts" / "extract_dossier.py"
FIXTURE_ROOT = ROOT / "skills" / "grader" / "fixtures" / "fake_claude"


def test_cli_builds_dossier_from_fixture_tree(tmp_path):
    # Arrange: fake ~/.claude/projects/...
    projects = tmp_path / "projects" / "demo"
    projects.mkdir(parents=True)
    src = ROOT / "skills" / "grader" / "fixtures" / "sessions" / "weak_vague.jsonl"
    (projects / "weak_vague.jsonl").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--limit", "30"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["intake_path"] == "auto"
    assert data["sessions_graded"] == 1
    assert data["sessions"][0]["user_prompts"][0] == "fix it"


def test_cli_exits_2_when_no_sessions(tmp_path):
    (tmp_path / "projects").mkdir()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_cli_export_path():
    export = ROOT / "skills" / "grader" / "fixtures" / "exports" / "weak_export.md"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--export", str(export)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["intake_path"] == "export"
    assert data["sessions"][0]["prompt_count"] == 2


def test_cli_export_path_respects_prompt_limit(tmp_path):
    export = tmp_path / "many_export.md"
    export.write_text(
        "\n\n".join([
            "## session 2026-07-01T00:00:00Z\nUser: old-1\nUser: old-2\nUser: old-3",
            "## session 2026-07-02T00:00:00Z\nUser: new-1\nUser: new-2\nUser: new-3",
        ]),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--export", str(export), "--prompt-limit", "4"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["prompts_sampled"] == 4
    assert data["prompts_available"] == 6
    assert data["sessions_scanned"] == 2
