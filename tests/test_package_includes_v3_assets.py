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
    assert "grader/curriculum/lessons/model-fit-meta.md" in names
    assert "grader/scripts/score_math.py" in names
    assert "grader/scripts/finalize_grade.py" in names
    assert "grader/scripts/judge_schema.py" in names
    assert "grader/scripts/normalize.py" in names
    # v2 modules (history_lib, profile_schema, render_*, coach_tasks) are
    # optional straggler leftovers; package_for_desktop may include them, but
    # the v3 skill does not require them.
