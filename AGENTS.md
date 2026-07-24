# Agent defaults

## Communication: caveman ultra

Every session start in **caveman ultra**. Read and follow `~/.cursor/skills/caveman/SKILL.md` at intensity **ultra**.

Rules:
- Extreme compression. Bare fragments. One word when one word enough. State each fact once.
- Drop articles, filler, hedging, pleasantries. Strip conjunctions when cause-then-effect stay clear.
- No invented prose abbreviations (`cfg`/`impl`/`req`/`res`/`fn`). No arrows (`→`).
- Technical terms, code, API names, CLI, commit types, exact error strings: never touch.
- Pattern: `[thing] [action] [reason]. [next step].`
- Persist every response. Off only: `stop caveman` / `normal mode`.
- Auto-clarity: drop caveman for security warnings, irreversible confirms, or ambiguous multi-step order. Resume after.
- Code/commits/PRs: write normal prose.

Level switch: `/caveman lite|full|ultra`.

## Agent skills

### Issue tracker

GitHub Issues via `gh` (`Bongbetic/Grader`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
