from pathlib import Path
import zipfile

from package_for_desktop import package


def test_package_includes_flows_and_renderers(tmp_path):
    skill = Path(__file__).resolve().parents[1] / "skills" / "grader"
    out = tmp_path / "grader.zip"

    package(skill, out)

    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())

    assert "grader/flows/grade.md" in names
    assert "grader/scripts/render_report.py" in names
    assert "grader/scripts/render_trends.py" in names
    assert "grader/scripts/history_lib.py" in names
    assert "grader/references/coach_tasks.json" in names
