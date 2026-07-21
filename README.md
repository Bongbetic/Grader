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
