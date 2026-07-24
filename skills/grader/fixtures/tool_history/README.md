# Tool history fixtures

Fixture paths mirror the documented allowlist layout for each tool.

- `.codex/sessions/**/*.jsonl` — Codex session transcripts (rollout JSONL with `type`/`payload`, or legacy `text`/`prompt` lines).
- `.cursor/grader-import/**/*.jsonl` — Cursor exported transcripts.
- `.cursor/projects/**/agent-transcripts/<uuid>/<uuid>.jsonl` — Cursor nested agent transcripts (also flat `*.jsonl` / `*.json` / `*.txt` under that tree).
- `AppData/Roaming/Code/User/globalStorage/github.copilot*/**/*chat*` — Copilot chat storage (best-effort, may be binary or JSON).
