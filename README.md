<p align="center">
  <img src="assets/bongbetic-wordmark-dark.png" alt="Bongbetic — Grader prompt-learning coach" width="480" />
</p>

<h1 align="center">Grader — Learn to Prompt Better</h1>

<p align="center">
  <strong>Open-source, local-first prompt engineering coach for AI coding assistants</strong><br/>
  Grade · Coach · Practice · Trends — powered by a research-backed 11-dimension rubric
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+" /></a>
  <a href="https://github.com/Bongbetic/Grader"><img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg" alt="macOS, Linux, Windows" /></a>
</p>

---

## 🔍 What is Grader?

**Grader** is a free, open-source **agent skill** for **Claude Code**, **Cursor**, **OpenAI Codex CLI**, and **GitHub Copilot**. It helps engineering students (and busy developers) **learn prompt engineering from real prompts** they already wrote while building projects.

**The agent you install Grader on is the judge.** Cursor grades in Cursor. Codex grades in Codex. Claude Code grades in Claude Code. Python handles the math, storage, and privacy — your coding agent handles rubric scoring.

Unlike generic prompt checklists, Grader:

- 📂 **Reads your local chat history** (with explicit per-tool consent) from **Claude Code**, **Cursor**, **GitHub Copilot**, and **OpenAI Codex**
- 📋 **Scores each prompt** against an **11-dimension research rubric** (D1–D11) with letter grades A–D
- 🧑‍🏫 **Coaches rewrites** with dimension-specific teaching notes and linked lessons
- 🏋️ **Runs practice drills** targeting your weakest dimensions
- 📈 **Tracks progress** over time with local trend metrics

> 🔒 **Privacy first:** You stay in control. Nothing is uploaded to third parties. Secrets and emails are redacted before scoring or storage. Raw transcripts are purged after 30 days.

> 🚫 **Not a token meter.** Grader does not use token counts, cost, latency, or model tier as grading inputs.

## 🙌 Who it’s for

Grader is for:

- **Engineering students** learning to prompt Claude Code and other coding assistants so they get better, more testable results
- **Developers** using AI coding tools daily who want clear, repeatable improvement feedback
- **Learners** with local chat history (or exports) they can review with explicit consent

If you just want a one-off prompt tweak, skip the history scan and use the paste/import path instead.

---

## 📑 Table of contents

- [Host vs intake](#-host-vs-intake-two-roles)
- [Supported AI coding tools](#-supported-ai-coding-tools)
- [Four learning flows](#-four-learning-flows)
- [Quick start](#-quick-start)
- [Install the Grader skill](#-install-the-grader-skill)
  - [Any host (auto-detect)](#-any-host-auto-detect-recommended)
  - [Cursor](#-cursor)
  - [Claude Code](#-claude-code)
  - [OpenAI Codex CLI](#-openai-codex-cli)
  - [GitHub Copilot](#-github-copilot)
  - [Claude Desktop / claude.ai](#-claude-desktop--claudeai)
- [Grade prompts from each tool](#-grade-prompts-from-each-tool)
  - [Claude Code](#1-claude-code)
  - [OpenAI Codex CLI](#2-openai-codex-cli)
  - [Cursor](#3-cursor)
  - [GitHub Copilot](#4-github-copilot)
  - [ChatGPT, Gemini & paste/import](#5-chatgpt-gemini--pasteimport)
- [Using the four flows](#-using-the-four-flows)
- [Privacy & data retention](#-privacy--data-retention)
- [Requirements](#-requirements)
- [Development](#-development)
- [GitHub topics](#-github-topics)
- [License](#-license)

---

---

## 🧠 Host vs intake (two roles)

Grader has two separate ideas — don't mix them up:

| Role | What it means | Examples |
|------|---------------|----------|
| **Host** (where Grader runs + judges) | Install the skill here. **This agent scores your prompts.** | Cursor, Claude Code, Codex CLI, Copilot |
| **Intake** (where prompts come from) | Grader reads local history from here (with consent) | Claude, Cursor, Codex, Copilot, paste/import |

You can **run Grader in Cursor** and **grade prompts from Copilot history**. The host always judges; intake is just the source.

---

## 🤖 Supported AI coding tools

### Hosts (install Grader + judge here)

| Host | Install path | Invoke |
|------|--------------|--------|
| **Cursor** | `~/.cursor/skills/grader` | `/grader` or "grade my prompts" |
| **Claude Code** | `~/.claude/skills/grader` | `/grader` |
| **OpenAI Codex CLI** | `~/.codex/skills/grader` (+ `~/.agents/skills/grader`) | `/grader` or `$grader` |
| **GitHub Copilot** | `~/.github/skills/grader` | skill invocation per Copilot |
| **Claude Desktop** | upload ZIP (see below) | enable skill + ask |

### Intake sources (grade prompts from here)

Grader reads allowlisted local history (or pasted exports) from:

| Tool | Auto-discover history | Platform | Consent token | History location |
|------|----------------------|----------|---------------|------------------|
| **Claude Code** | ✅ Yes | macOS, Linux, Windows | `claude` | `~/.claude/projects/**/sessions/*.jsonl` |
| **OpenAI Codex CLI** | ✅ Yes | macOS, Linux, Windows | `codex` | `~/.codex/sessions/**/*.jsonl` (or `$CODEX_HOME`) |
| **Cursor** | ✅ Yes | macOS, Linux, Windows | `cursor` | `~/.cursor/projects/**/agent-transcripts/<uuid>/<uuid>.jsonl` (nested) and `~/.cursor/grader-import/` |
| **GitHub Copilot** | ⚠️ Best-effort | Windows (VS Code) | `copilot` | `%APPDATA%\Code\User\globalStorage\github.copilot*\**\*chat*` |
| **ChatGPT / Gemini / others** | 📋 Paste/import | Any | — | Paste or export into the skill session |

---

## 🎯 Four learning flows

| Flow | Trigger phrases | What you get |
|------|-----------------|--------------|
| **📊 Grade** | `/grader`, "grade my prompt", "run grader" | Letter grade, percent, per-dimension feedback on up to 100 recent prompts |
| **🧑‍🏫 Coach** | "coach me", "help me improve prompting", "live assessment" | Teaching notes + lesson links + guided rewrite on your weakest dimensions |
| **🏋️ Practice** | "practice prompting", "give me exercises", "drill me" | Targeted drills with feedback; optional exemplar building |
| **📈 Trends** | "show my trends", "my progress", "prompt history" | Progress charts from persisted local grades |

The skill router lives in [`skills/grader/SKILL.md`](skills/grader/SKILL.md). Each flow is a playbook in [`skills/grader/flows/`](skills/grader/flows/).

---

## ⚡ Quick start

```bash
# 1. Clone and install dependencies
git clone --depth 1 https://github.com/Bongbetic/Grader.git
cd Grader
python3 -m pip install -r requirements.txt

# 2. Install for the coding agent you're using (auto-detect)
python3 skills/grader/scripts/install_skill.py --host auto

# 3. Open your coding agent and run
/grader
```

If auto-detect fails, pass `--host cursor`, `--host claude`, `--host codex`, or `--host copilot`.

Then say **"grade my prompts"**, **"coach me"**, **"practice prompting"**, or **"show my trends"**.

---

## 🤖 If you're a coding agent (GitHub landing auto-install)

If someone lands on this GitHub URL, **detect which agent you are** and install Grader for that host. **You will be the judge** — score prompts yourself per `references/rubric-sheet.md` and pass JSON to `scripts/finalize_grade.py`.

From the repo root (`Grader/`):

```bash
python3 -m pip install -r requirements.txt
python3 skills/grader/scripts/install_skill.py --host auto
```

If auto-detect fails, pick the host explicitly:

| You are running in… | Command |
|---------------------|---------|
| **Cursor** | `python3 skills/grader/scripts/install_skill.py --host cursor` |
| **Claude Code** | `python3 skills/grader/scripts/install_skill.py --host claude` |
| **Codex CLI** | `python3 skills/grader/scripts/install_skill.py --host codex` |
| **GitHub Copilot** | `python3 skills/grader/scripts/install_skill.py --host copilot` |
| **Unsure / CI** | `python3 skills/grader/scripts/install_skill.py --host all` |

Then invoke `/grader` (or natural language) in the same agent session.

### Claude Desktop / claude.ai (optional)

```bash
python3 skills/grader/scripts/package_for_desktop.py --out ~/Downloads/grader.zip
```

Upload the ZIP as a skill. For **Grade**, paste prompts when asked.

---

## 📦 Install the Grader skill

Grader installs as an **agent skill** on your coding tool. The tool you install on becomes the **judge**.

### ⚡ Any host (auto-detect, recommended)

```bash
git clone --depth 1 https://github.com/Bongbetic/Grader.git
cd Grader
python3 -m pip install -r requirements.txt
python3 skills/grader/scripts/install_skill.py --host auto
```

### 🖱️ Cursor

**macOS / Linux:**

```bash
python3 skills/grader/scripts/install_skill.py --host cursor
```

**Windows (PowerShell):**

```powershell
python3 skills/grader/scripts/install_skill.py --host cursor
```

**Verify:** Open Cursor Agent and type `/grader`.

Install path: `~/.cursor/skills/grader`

### 🖥️ Claude Code

**macOS / Linux:**

```bash
python3 skills/grader/scripts/install_skill.py --host claude
```

**Windows (PowerShell):**

```powershell
python3 skills/grader/scripts/install_skill.py --host claude
```

**Verify:** Open Claude Code and type `/grader`.

Install path: `~/.claude/skills/grader`

### 🤖 OpenAI Codex CLI

```bash
python3 skills/grader/scripts/install_skill.py --host codex
```

Install paths: `~/.codex/skills/grader` and `~/.agents/skills/grader`

### 🐙 GitHub Copilot

```bash
python3 skills/grader/scripts/install_skill.py --host copilot
```

Install path: `~/.github/skills/grader`

> Copilot chat history intake is best-effort on Windows. You can still grade pasted prompts in any host.

### 🌐 Claude Desktop / claude.ai

Claude Desktop cannot read local tool history directly. Use it for **Coach**, **Practice**, and **Trends**, or **paste** exported prompts for **Grade**.

1. **Build the upload ZIP:**

   ```bash
   python3 skills/grader/scripts/package_for_desktop.py --out ~/Downloads/grader.zip
   ```

2. In Claude Desktop: **Settings → Capabilities → enable Code execution and file creation**
3. **Customize → Skills → Upload a skill** → choose `grader.zip`
4. Confirm the ZIP unpacks to `grader/SKILL.md` (not loose files at the root)
5. Toggle **grader** on and ask for any flow

> 💡 **Tip:** Export prompts from Cursor, Copilot, or Codex and paste them when Grader asks. Desktop grading works great with the paste/import path.

---

## 🔧 Grade prompts from each tool

For every auto-discover tool, Grader follows the same pattern:

1. **Grant consent** (one-time per tool)
2. **Scan** allowlisted local history
3. **Review** the scan summary (count, date range, redactions)
4. **Confirm** to proceed → Grader judges and finalizes grades

All commands below run from the skill directory (`~/.cursor/skills/grader`, `~/.claude/skills/grader`, etc., or `skills/grader` in the repo).

### 1. Claude Code

Reads your local Claude Code session logs.

```bash
# Grant consent (one-time)
python3 scripts/grant_consent.py --tool claude

# Preview what Grader will read
python3 scripts/scan_intake.py --tools claude --json
```

Then in Claude Code:

```
/grader grade my recent Claude Code prompts
```

**History path:** `~/.claude/projects/<project>/sessions/*.jsonl`

---

### 2. OpenAI Codex CLI

Reads local Codex session transcripts.

```bash
python3 scripts/grant_consent.py --tool codex
python3 scripts/scan_intake.py --tools codex --json
```

```
/grader grade my Codex prompts
```

**History path:** `~/.codex/sessions/**/*.jsonl` (override with `$CODEX_HOME`)

---

### 3. Cursor

Reads Cursor agent/composer transcripts and any files you export for Grader.

**Automatic discovery** (agent transcripts):

```bash
python3 scripts/grant_consent.py --tool cursor
python3 scripts/scan_intake.py --tools cursor --json
```

```
/grader grade my Cursor prompts
```

**History paths:**

- `~/.cursor/projects/<workspace>/agent-transcripts/<uuid>/<uuid>.jsonl` (nested layout; also flat `*.jsonl` / `*.json` / `*.txt` under that tree)
- `~/.cursor/grader-import/**/*.jsonl` (manual exports)

**Manual export (optional):** Copy or export Cursor chat transcripts into `~/.cursor/grader-import/` as `.jsonl` files, then scan again.

---

### 4. GitHub Copilot

Best-effort discovery of Copilot chat history from VS Code on Windows.

```bash
python3 scripts/grant_consent.py --tool copilot
python3 scripts/scan_intake.py --tools copilot --json
```

```
/grader grade my Copilot prompts
```

**History path:** `%APPDATA%\Code\User\globalStorage\github.copilot*\**\*chat*`

> ⚠️ Copilot storage formats vary by VS Code version. Grader may report `partial: true` if some files cannot be parsed. Paste individual prompts as a fallback.

---

### 5. ChatGPT, Gemini & paste/import

Server-side tools have no local history path. **Paste or import** your prompts directly:

```
/grader grade this prompt:

<paste your prompt here>
```

Or scan multiple tools in one session:

```bash
python3 scripts/grant_consent.py --tool claude
python3 scripts/grant_consent.py --tool cursor
python3 scripts/scan_intake.py --tools claude,cursor,codex --json
```

---

## 🎓 Using the four flows

### 📊 Grade (default)

```
/grader
grade my last 10 Cursor prompts
```

Grader will: check consent → scan history → show summary → ask you to proceed → judge each prompt → report letter grade, percent, and per-dimension rationales.

### 🧑‍🏫 Coach

```
coach me on my weakest dimension
```

Requires a graded prompt in-session. Grader loads teaching notes, links the matching lesson from `curriculum/lessons/`, and guides a rewrite.

### 🏋️ Practice

```
practice prompting on specificity
give me a drill for D3
```

Grader picks your weakest dimension (from trends if available), generates a realistic exercise, judges your attempt, and records the session locally.

### 📈 Trends

```
show my trends
how am I improving?
```

Requires a few graded sessions. Grader prints progress metrics from `~/.grader/metrics.jsonl`.

---

## 🔒 Privacy & data retention

| Policy | Detail |
|--------|--------|
| **Consent gate** | Per-tool consent required before any history read |
| **Redaction** | API keys, tokens, secrets, and emails redacted before scoring or storage |
| **Local-only** | Data stored under `~/.grader/` on your machine |
| **30-day purge** | Raw transcripts and excerpts auto-purged; trend metrics kept |
| **No third-party upload** | Host model sees redacted text only; no external API calls |
| **User purge** | `python3 scripts/purge_data.py --user-purge` clears your data on demand |

---

## 📋 Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| git | any recent |
| Coding-agent host | Cursor, Claude Code, Codex CLI, GitHub Copilot, or Claude Desktop (with code execution) |

---

## 🛠️ Development

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -v
```

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) for how to contribute, coding conventions, and per-agent install steps.

Key doc:

- [`prompt-quality-research-and-rubric.md`](prompt-quality-research-and-rubric.md) — rubric research

---

## 🏷️ GitHub topics

If you fork or star this repo, these topics help others discover Grader:

`prompt-engineering` · `ai-coding-assistant` · `claude-code` · `claude-skill` · `cursor` · `github-copilot` · `openai-codex` · `prompt-grading` · `developer-tools` · `learning` · `rubric` · `local-first` · `privacy`

---

## 📄 License

MIT License — Copyright (c) 2026 Bongbetic and Soubarna. See [`LICENSE`](LICENSE).

## 🤝 Code of conduct

This project follows the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
