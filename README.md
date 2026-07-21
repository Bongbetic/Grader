# Grader

Claude Code skill that grades recent prompting quality (A–D). See `docs/superpowers/specs/2026-07-21-grader-design.md`.

## Install (personal Claude Code skill)

Windows (PowerShell):
```powershell
Copy-Item -Recurse -Force skills\grader $env:USERPROFILE\.claude\skills\grader
```

macOS/Linux:
```bash
cp -R skills/grader ~/.claude/skills/grader
```

Invoke in Claude Code: `/grader`

## Dev tests
```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

## Acceptance (Task 10)

- Skill package complete under `skills/grader/` (`SKILL.md`, `checklist.md`, `signals.md`, scripts, fixtures, references)
- Path A auto-dig: `extract_dossier.py --root <fixture>` (see `tests/test_extract_cli.py`)
- Path B fallback: `extract_dossier.py --export skills/grader/fixtures/exports/weak_export.md`
- Empty root or zero sessions → exit code `2`
- Fixture theme expectations: `skills/grader/fixtures/expected/{weak,strong}_grade_themes.md`
- No token/cost language in skill docs except forbidden-list mentions in `signals.md`
