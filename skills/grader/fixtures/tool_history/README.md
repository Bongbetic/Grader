# Tool history fixtures

Fixture paths mirror the documented allowlist layout for each tool.

- `.codex/sessions/**/*.jsonl` — Codex session transcripts (rollout JSONL with `type`/`payload`, or legacy `text`/`prompt` lines).
- `.cursor/grader-import/**/*.jsonl` — Cursor exported transcripts.
- `.cursor/projects/**/agent-transcripts/*` — Cursor composer/agent transcripts (`.jsonl`, `.json`, `.txt`).
- `AppData/Roaming/Code/User/globalStorage/github.copilot*/**/*chat*` — Copilot chat storage (best-effort, may be binary or JSON).
