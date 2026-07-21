# Best-practices reference policy

## Purpose

The grader scores against the distilled **`checklist.md`** rubric. A full Anthropic or user-authored best-practices document (e.g. `Best prompting Practices.md`) is **optional background** — not a line-by-line scoring source.

## Rules

1. **Do not score line-by-line** against the full best-practices doc. Every grade must trace to checklist dimensions and dossier evidence.
2. **Checklist is authoritative** for v1. The eight dimensions in `checklist.md` are the only scored craft categories.
3. **Reference doc is clarifying only.** If the user attaches or links a long best-practices guide:
   - Use it to interpret checklist intent (what “success criteria” or “agentic hygiene” means in their context).
   - Do not add new dimensions, weights, or pass/fail rules from the reference.
   - Do not quote the reference as a checklist item the user “failed.”
4. **No token/cost content** from any reference doc may enter the grade or report (see `signals.md` forbidden metrics).
5. **Historical prompts, not system-prompt engineering.** The reference may discuss API system prompts; this grader evaluates **user messages in Claude Code sessions** only.

## When the user provides the full doc

- Skim for alignment with checklist dimensions; do not produce a coverage matrix.
- If the reference suggests a practice that maps clearly to one checklist dimension, cite that dimension in gaps/strengths — not the reference section number.
- If the reference contradicts `checklist.md`, follow `checklist.md`.

## Bundling

The skill may ship without bundling the full best-practices file. If bundled under `references/`, treat it as read-only context for the grader agent, not an additional rubric file.
