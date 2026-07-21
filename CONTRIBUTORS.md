# Contributors guide

Thanks for helping improve **Grader** — a Claude Code skill that coaches vibecoders on prompting craft.

This doc explains **how the code is structured**, the rules that keep it consistent, and how to land a change.

---

## Who this project is for

Grader targets **vibecoders** who ship with Claude Code and want sharper prompts, fewer correction loops, and a practice loop — not a token/cost dashboard.

Keep that audience in mind when you change copy, flows, or UX.

---

## Architecture at a glance

```text
skills/grader/                 # the installable Claude skill (folder name MUST stay "grader")
  SKILL.md                     # intent router + hard gates + shared dig procedure
  checklist.md                 # craft rubric (Prompt DNA dimensions)
  signals.md                   # light modifiers + forbidden metrics
  flows/                       # Grade / Coach / Practice / Trends playbooks (LLM procedures)
  references/                  # coach task bank, optional policy docs
  scripts/                     # Python: collect, analyze, history, render, package
  fixtures/                    # sample sessions / exports / profiles for tests

tests/                         # pytest (repo root); scripts/ is on sys.path via conftest
README.md                      # product + install for users
```

### Mental model: five layers

| Layer | Lives in | Owns |
|-------|----------|------|
| **Collector** | `grader_lib.py`, `extract_dossier.py` | Dig `~/.claude` / export; redact; truncate; **100-prompt** sample |
| **Analyzer** | `grader_lib.py` (+ LLM via checklist) | Task segmentation, **efficiency** aggregates (Python); craft judgment (LLM) |
| **Coach** | `flows/*.md`, `coach_tasks.py` | Live tasks, learning cards, practice packs |
| **Renderer** | `render_report.py`, `render_trends.py` | Self-contained HTML (inline CSS/SVG, **no CDN**) |
| **History** | `history_lib.py` | Coach completions; trends unlock at **5** completed sessions |

**Rule of thumb:** Python owns **deterministic math** (sampling, Jaccard/segmentation, efficiency, unlock gates, HTML). The LLM owns **craft judgment** (DNA verdicts, habits, coaching copy) driven by markdown playbooks.

Shared hand-off shape: **profile JSON** (`profile_schema.py`) → markdown report and/or HTML.

---

## Hard product constraints (do not break)

- Skill command/folder stays **`grader` / `/grader`** — do not rename to coach.
- **No** token / cost / spend / cache / latency / model-tier scoring.
- Efficiency = **prompts-per-task** conversation efficacy, reported **separate** from Skill.
- Sample unit = **100 prompts** newest-first (`DEFAULT_PROMPT_LIMIT`); session scan ceiling = 100.
- Trends unlock only after **5** Coach sessions with live assessment finished **and** ≥1 coaching drill round.
- Evidence must cite real `session#/prompt#` (or live-task ids).
- HTML must be **offline / self-contained** (no external `http(s)` assets).
- Runtime Python = **stdlib only**; `pytest` is test-only via `requirements.txt`.
- History is **local** under `{claude_root}/skills/grader/history/`.

---

## How code is written here

### Python (`skills/grader/scripts/`)

- Prefer small, focused modules with clear public functions (see existing `grader_lib`, `history_lib`, `profile_schema`).
- Type hints on public APIs; `from __future__ import annotations`.
- Reuse helpers (`_tokens`, `_jaccard`, `compute_signals`) instead of reimplementing overlap logic.
- Keep side effects at the edges (CLI `main()`, file append for history).
- Escape all user-derived strings in HTML (`html.escape`).
- New behavior → **pytest first** (TDD). Put tests under `tests/test_*.py`.

### Skill markdown (`SKILL.md`, `flows/`, `checklist.md`, `signals.md`)

- Playbooks are procedures for the model: concrete steps, exact CLI commands, completion rules.
- Don’t invent new letter axes without updating checklist + profile schema + renderers together.
- Preserve hard gates wording when editing `SKILL.md` / `signals.md`.

### Tests

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -v
```

`tests/conftest.py` adds `skills/grader/scripts` to `sys.path`. Prefer tmp_path fixtures over mutating real `~/.claude`.

### Packaging

```bash
python3 skills/grader/scripts/package_for_desktop.py
```

ZIP root must be `grader/…`. If you add flows/scripts/references, extend `tests/test_package_includes_coach_assets.py` when those assets are load-bearing.

---

## Local setup for contributors

1. Fork + clone the repo.  
2. Python **3.11+**.  
3. `python3 -m pip install -r requirements.txt`  
4. Run tests (above).  
5. Optional: install the skill locally for manual Claude Code trials:

```bash
mkdir -p ~/.claude/skills
rm -rf ~/.claude/skills/grader
cp -R skills/grader ~/.claude/skills/grader
```

---

## Contribution workflow

1. **Open an issue** (or comment on one) for non-trivial changes — especially rubric, scoring, or flow behavior.  
2. Branch from `main` (`feat/…`, `fix/…`, or `docs/…`).  
3. Keep PRs focused: one concern per PR when possible.  
4. Include tests for collector/analyzer/history/renderer changes.  
5. Update `README.md` if user-facing behavior or install steps change.  
6. Do **not** commit secrets, real user transcripts, or local `~/.claude` dumps.  
7. Do **not** add `docs/` planning scratch to git — that directory is gitignored.

### PR checklist

- [ ] `python3 -m pytest -v` passes  
- [ ] No token/cost metrics introduced  
- [ ] New scripts/assets still pack into `grader.zip` if Desktop-relevant  
- [ ] Skill folder still named `grader`  
- [ ] User-facing copy still speaks to vibecoders / Claude Code prompting  

---

## Good first contributions

- More coach tasks in `references/coach_tasks.json` (keep schema: `id`, `complexity`, `title`, `problem`, `must_cover`, `failure_modes`)  
- Fixture sessions for mid-grade / high-rework edge cases  
- Clearer learning-card examples in flow docs  
- Accessibility polish in HTML renderers (still no external fonts/CDN)  
- Windows install-script fixes in `README.md`  

---

## What not to add (for now)

- Cloud sync / accounts  
- Multi-model collectors (ChatGPT, Gemini, …) as first-class intake  
- Confidence %, archetype benchmarks, or anti-pattern brand catalogs (unless agreed in an issue)  
- Dependency-heavy visual stacks (React, chart CDNs, etc.)  

---

## Questions

Open a GitHub issue on [Bongbetic/Grader](https://github.com/Bongbetic/Grader). Prefer a short repro (fixture + expected vs actual) for bugs in sampling, efficiency math, history unlock, or HTML output.
