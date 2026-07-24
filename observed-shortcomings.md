# Grader skill — observed shortcomings

Findings from a live `/grader` run on Cursor history (Jul 2026). Includes bugs hit in production, scoring gaps, and missing features relative to the v3 tri-pane design (Craft · Efficacy · Planning).

**Status key:** `fixed` = landed in repo (epic #15 / children #16–#22) · `open` = not yet addressed · `partial` = mitigated but incomplete · `wontfix` = accepted limitation

Epic #15 lands multi-tool intake + tri-pane + judge-consistency (children #16–#22). Rows below reflect post-land status.

---

## 1. Intake & adapters

| ID | Status | Shortcoming | Impact |
|----|--------|-------------|--------|
| I-01 | fixed | Cursor allowlist missed nested `agent-transcripts/<id>/<id>.jsonl`. | Was: 0 scan candidates. Now: `allowlist` `rglob` under `agent-transcripts`. |
| I-02 | fixed | Cursor JSONL parser expected flat `text` / `message`; real shape is `{role, message: {content: [{type, text}]}}`. | Cursor-specific parser in `adapters/cursor.py`. |
| I-03 | fixed | User text inside `<user_query>` plus inlined skill/system blocks graded as-is. | Shared `sanitize_learner_text()` on all adapters. |
| I-04 | partial | Scan `time_range` null for Cursor (no per-turn timestamps in JSONL). | File `mtime` session-level fallback landed; per-turn timestamps remain unavailable (`wontfix`). |
| I-05 | fixed | Scan candidate count vs full corpus confusing (`limit` sessions). | Scan summary surfaces limit vs total discovered. |
| I-06 | fixed | `workflow_protocol_reply` filtered by ad hoc prefix denylist. | Classifier-driven via shared sanitizer + rubric classification. |
| I-07 | fixed | Hooks, MCP meta, subagent boilerplate not stripped. | Shared sanitizer strips before normalize. |
| I-08 | open | `~/.cursor/grader-import` documented; no guided Cursor UI export. | Paste/import remains manual fallback when auto-scan fails. Tracked: #29 (parent #23). |

---

## 2. Craft scoring (D1–D11)

| ID | Status | Shortcoming | Impact |
|----|--------|-------------|--------|
| C-01 | fixed | Proportionality lens under-applied for terse trivial/simple tasks. | `grade.md` + `rubric-sheet.md` require classification block; D1/D3/D6 proportional. |
| C-02 | open | Length still correlates with score in practice (host-judge bias). | Policy + gold fixtures mitigate; host models may still over-weight length. Tracked: #26 (parent #23). |
| C-03 | fixed | D2 under-scored for valid continuations. | Proportionality scores D2 for `valid_continuation`; gold fixture `fair-terse-valid-continuation`. |
| C-04 | fixed | `target_model_class` often `unknown` for Cursor — D5 excluded; model-fit coaching weak. | `model_class.resolve` + grade flow prompt before finalize; AS-005 disclosed when skip. Tracked: #24 (parent #23). |
| C-05 | fixed | Large batches used heuristic judge scripts. | Policy forbids heuristic learner-facing grades; host-LLM JSON per prompt required (`judge-consistency.md`). |
| C-06 | fixed | No official batch grade path — hosts improvised scripts. | Sample ≤30 default + `--reports-manifest` playbook in `grade.md`. |

---

## 3. Efficacy & Planning axes

| ID | Status | Shortcoming | Impact |
|----|--------|-------------|--------|
| E-01 | fixed | Efficacy/Planning `unavailable` for Cursor grade flow. | `build_session_outcome` + grade flow for claude/cursor/codex. |
| E-02 | fixed | Cursor `assistant_text=False` dropped assistant turns. | Capability matrix `assistant_text=True` for session-capable tools that preserve turns. |
| E-03 | fixed | No `discover_turns()` for Cursor. | `discover_turns` on claude, cursor, codex. |
| E-04 | fixed | Grade flow omitted `--efficacy-json` / `--planning-json` for Cursor. | Wired for all session-capable tools via `build_session_outcome`. |
| E-05 | fixed | Efficacy attribution not wired; Cursor omits tool outputs. | Wired with assistant turns; `tool_or_environment` capped at medium when outputs absent. |
| E-06 | fixed | Planning scope-change labels never produced for Cursor. | Planning JSON from segmented turns for session-capable tools. |

---

## 4. Tooling & platform

| ID | Status | Shortcoming | Impact |
|----|--------|-------------|--------|
| T-01 | fixed | Windows `WinError 206` on 500+ CLI report paths. | `--reports-manifest` JSON path list. |
| T-02 | fixed | Temp artifacts left after ad hoc batch runs. | Retention/cleanup policy in grade flow / SKILL. |
| T-03 | fixed | PowerShell older versions lack `&&`. | SKILL.md documents PS 5.1 (`;`) and PS 7+ (`&&`). |
| T-04 | fixed | Fixtures used flat `agent-transcripts/*.jsonl` only. | Nested Cursor fixture + regression test for flat-only glob miss. |

---

## 5. UX & flow gaps

| ID | Status | Shortcoming | Impact |
|----|--------|-------------|--------|
| U-01 | fixed | No recommended sample size for large corpora. | Default ≤30 with learner opt-in for full corpus. |
| U-02 | open | No per-prompt drill-down UI after batch (session rollup only). | Tracked: #27 (parent #23). |
| U-03 | open | `trends_report.py` noisy after bulk persist. | Tracked: #28 (parent #23). |
| U-04 | fixed | Coach/Practice offer skipped when batch consumed the session. | Grade flow §6 required after batch/rollup (incl. ≤30 sample). Tracked: #25 (parent #23). |

---

## 6. Recommended fix priority (post-#15)

Parent epic: **#23**. Queue lives on GitHub — not this table alone.

1. **Frontier (shipped):** #24 (C-04), #25 (U-04) — closed via `/implement`.
2. **Grill first:** #29 (I-08), #26 (C-02), #27 (U-02), #28 (U-03).
3. On each close: flip ID to `fixed` here in the same commit.

---

## 7. Live-install patches (now in repo)

| File | Change | Repo status |
|------|--------|-------------|
| `skills/grader/scripts/allowlist.py` | Nested `agent-transcripts` discovery via `rglob`. | **fixed** (#16) |
| `skills/grader/scripts/adapters/cursor.py` | Cursor JSONL shape + shared sanitizer. | **fixed** (#16) |
| `skills/grader/scripts/sanitize.py` | Shared learner-text sanitizer. | **fixed** (#16) |
| `skills/grader/scripts/build_session_outcome.py` | Multi-tool tri-pane wire. | **fixed** (#17/#18) |
| `skills/grader/references/judge-consistency.md` | Deterministic vs stochastic contract. | **fixed** (#22) |

---

## 8. Evidence sources

- Live `/grader grade my prompts` run on Cursor history (consent granted) — Jul 2026 baseline.
- Epic #15 children #16–#22 closed on `main`.
- `skills/grader/scripts/capability_matrix.py`, `finalize_grade.py`, `flows/grade.md`, `references/rubric-sheet.md`, `references/judge-consistency.md`.

---

*Generated from operational findings — not an official product roadmap. Updated when epic #15 landed.*
