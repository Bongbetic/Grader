# Contributors guide

Thanks for helping improve **Grader v3** — a local, open-source prompt-learning coach for AI coding assistants.

This file is the **how to contribute** guide for humans and coding agents. It is separate from GitHub’s automatic **Contributors** list (commit authors only).

---

## Who this project is for

Grader helps students and builders learn to write sharper prompts for **Claude Code**, **Cursor**, **GitHub Copilot**, **OpenAI Codex**, and other AI coding tools. Keep that learner-first voice in copy, flows, and scoring.

---

## How to contribute to this repo

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/Grader.git
cd Grader
git remote add upstream https://github.com/Bongbetic/Grader.git
```

### 2. Set up your environment

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -v
```

Python **3.11+** required. Runtime code is **stdlib only**; `pytest` is dev-only.

### 3. Install Grader on your coding agent (for manual trials)

The agent you install on **is the judge**. Pick your host:

| Host | Install command | Skill path |
|------|-----------------|------------|
| **Cursor** | `python3 skills/grader/scripts/install_skill.py --host cursor` | `~/.cursor/skills/grader` |
| **Claude Code** | `python3 skills/grader/scripts/install_skill.py --host claude` | `~/.claude/skills/grader` |
| **OpenAI Codex CLI** | `python3 skills/grader/scripts/install_skill.py --host codex` | `~/.codex/skills/grader`, `~/.agents/skills/grader` |
| **GitHub Copilot** | `python3 skills/grader/scripts/install_skill.py --host copilot` | `~/.github/skills/grader` |
| **Auto-detect** | `python3 skills/grader/scripts/install_skill.py --host auto` | detects from environment |

Then invoke `/grader` or ask naturally: “grade my prompts”, “coach me”, “practice prompting”, “show my trends”.

**Claude Desktop:** build a ZIP with `python3 skills/grader/scripts/package_for_desktop.py` and upload as a skill (see `README.md`).

### 4. Create a branch

```bash
git checkout -b feat/short-description
# or: fix/…, docs/…
```

Branch from `main`. Keep PRs focused — one concern per PR when possible.

### 5. Make changes + tests

- New behavior → **pytest first** (TDD). Tests live in `tests/test_*.py`.
- Use `tmp_path` fixtures — never mutate real `~/.grader` in tests.
- Update `README.md` if user-facing install or behavior changes.

### 6. Open a pull request

1. Push your branch to your fork.
2. Open a PR against `Bongbetic/Grader` `main`.
3. Fill in what changed and how you tested it.
4. Ensure CI passes (`python3 -m pytest -v`).

### PR checklist

- [ ] `python3 -m pytest -v` passes
- [ ] No token/cost/latency metrics introduced
- [ ] New Desktop-relevant assets still pack into `grader.zip` (extend `tests/test_package_includes_v3_assets.py` if needed)
- [ ] Skill folder still named `grader`
- [ ] User-facing copy speaks to learners and prompt improvement
- [ ] No secrets, real user transcripts, or `~/.grader` dumps committed

---

## Coding conventions

### Python (`skills/grader/scripts/`)

- Small, focused modules with clear public functions.
- Type hints on public APIs; `from __future__ import annotations`.
- Reuse helpers — do not reimplement logic.
- Side effects at the edges only (CLI `main()`, file I/O).
- Escape user-derived strings in HTML (`html.escape`).
- Match existing naming, imports, and error style in the file you edit.

### Skill markdown (`SKILL.md`, `flows/`, `references/`)

- Playbooks are procedures for the **host agent**: concrete steps, exact CLI commands, completion rules.
- The host agent scores prompts (judge JSON); Python recomputes percent/band/caps.
- Do not add dimensions or bands without updating `domain.py`, `score_math.py`, `judge_schema.py`, and renderers together.
- Preserve hard-gate wording in `SKILL.md` (no token metrics, consent first, redaction, four flows only).

### Commits

- Use clear, imperative subjects: `feat: …`, `fix: …`, `docs: …`, `test: …`.
- One logical change per commit when practical.

### What not to commit

- Secrets, API keys, real chat transcripts
- Local `~/.grader` data dumps
- Internal planning scratch (`docs/`, `v2plan.md`, `Grader-v3-*.md` — gitignored)
- `AGENTS.md` or other local-only agent config unless the maintainers ask for it

---

## Architecture

```text
skills/grader/                 # installable agent skill (folder name MUST stay "grader")
  SKILL.md                     # intent router + hard gates
  flows/                       # Grade / Coach / Practice / Trends playbooks
  scripts/                     # Python core
  curriculum/                  # lessons + seed exemplars
  references/                  # judge schema, rubric sheet
  fixtures/                    # sample sessions and test data
tests/                         # pytest (repo root)
README.md                      # user-facing install + usage
CONTRIBUTORS.md                # this file
```

### Core modules

| Module | Responsibility |
|--------|----------------|
| `domain.py` | Frozen dataclasses, enums, dimension weights |
| `score_math.py` | Pure weighted percent / band / cap computation |
| `judge_schema.py` | Validate structured judge JSON |
| `redact.py` | Secret + email redaction |
| `normalize.py` | Canonical `PromptRecord` |
| `model_class.py` | Infer target model class (`standard` / `reasoning` / `unknown`) |
| `consent.py` | Per-tool consent grant |
| `paths.py` | Resolve `~/.grader` store root |
| `store.py` | Atomic JSONL writes, grades, raw/excerpts, trend metrics |
| `retention.py` | 30-day purge of raw/excerpts |
| `allowlist.py` | Documented per-OS tool history paths |
| `adapters/` | Claude, Codex, Cursor, Copilot, import/paste intake |
| `install_skill.py` | Copy skill to host-specific skill directory |
| `scan_intake.py` | Consent-gated scan + summary JSON |
| `finalize_grade.py` | Judge JSON → `GradeReport` + persist |
| `purge_data.py` | Retention job + user purge |
| `teaching.py` | Fix text + lesson refs for weak dimensions |
| `curriculum.py` | Load lessons and exemplars |
| `practice_session.py` | Record practice attempts |
| `trends.py` / `trends_report.py` | Aggregate trends from store |
| `package_for_desktop.py` | Build `grader.zip` for Desktop upload |

### Split of responsibilities

- **Python owns:** deterministic math, scoring, persistence, redaction, consent, retention, adapters, HTML rendering, packaging.
- **Host agent (skill markdown) owns:** rubric judgment, coaching voice, practice exercises, Learner-facing instructions.

Hand-off: structured JSON from the host → `judge_schema` / `score_math` → `GradeReport`.

---

## Hard product constraints (do not break)

- Skill command/folder stays **`grader` / `/grader`** — do not rename it.
- **No** token / cost / spend / cache / latency / model-tier scoring.
- 11-dimension rubric from `prompt-quality-research-and-rubric.md` Part II.
- Bands: **A ≥ 90**, **B 75–89**, **C 60–74**, **D < 60**.
- Consent required before reading any tool history.
- Redact secrets and emails before storage or judge calls.
- 30-day retention for raw transcripts and excerpts; trend metrics survive.
- Store root is `~/.grader`.
- HTML must be self-contained; no external CDN or network assets.

---

## Testing

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -v
```

`tests/conftest.py` adds `skills/grader/scripts` to `sys.path`.

### Packaging check

```bash
python3 skills/grader/scripts/package_for_desktop.py
```

ZIP root must be `grader/…`.

---

## Good first contributions

- More seed exemplars in `curriculum/exemplars/seed/` (`id`, `dimension`, `before`, `after`, `origin`)
- Clearer lesson wording or teaching fixes
- Fixture sessions for multi-tool or edge cases
- Accessibility polish in HTML renderers (no external fonts/CDN)
- Adapter or allowlist fixes for new tool-history paths
- README install clarity for any supported host

---

## What not to add (for now)

- Cloud sync / accounts
- Server-side scraping of ChatGPT / Gemini history
- Confidence %, archetype benchmarks, or anti-pattern brand catalogs
- Dependency-heavy visual stacks (React, chart CDNs, etc.)

---

## Code of conduct

This project follows [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Be respectful in issues and PRs.

---

## Questions

Open a [GitHub issue](https://github.com/Bongbetic/Grader/issues). For bugs, include a short repro (fixture + expected vs actual).
