# Residual secret patterns past `redact.py`

**Ticket:** [Bongbetic/Grader#8](https://github.com/Bongbetic/Grader/issues/8)  
**Branch:** `research/residual-secret-redaction`  
**Date:** 2026-07-24

## Executive summary

The current redactor (`skills/grader/scripts/redact.py`) covers five pattern families: Anthropic keys, OpenAI-style `sk-` keys, GitHub classic PATs (`ghp_`), labeled generic secrets (`api_key` / `token` / `secret` with `:=`), and email addresses. Empirical tests against representative samples show **at least 17 high-likelihood secret formats leak unchanged**, including Coolify API tokens (`{id}|{hash}`), fine-grained GitHub PATs, Slack/Stripe/npm/GitLab prefixes, AWS access keys, JWTs, PEM private keys, and database URLs with embedded passwords.

The largest structural gaps are: (1) no `Bearer` header handling, (2) `generic_bearer` value charset excludes `|`, `.`, `/`, and `+` (breaking Sanctum, JWT, and URL secrets), and (3) no prefix-based rules beyond three vendors.

---

## 1. Current redactor — exact patterns caught

Source: `skills/grader/scripts/redact.py` lines 5–13.

| Label | Regex | Notes |
|-------|-------|-------|
| `anthropic_key` | `sk-ant-[A-Za-z0-9_-]{20,}` | Anthropic API keys ([`redact.py:6`](skills/grader/scripts/redact.py#L6)) |
| `openai_key` | `sk-[A-Za-z0-9]{20,}` | OpenAI-style keys; also matches any `sk-` + 20+ alnum ([`redact.py:7`](skills/grader/scripts/redact.py#L7)) |
| `github_pat` | `ghp_[A-Za-z0-9]{20,}` | GitHub classic PAT only ([`redact.py:8`](skills/grader/scripts/redact.py#L8)) |
| `generic_bearer` | `(?i)(api[_-]?key\|token\|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}` | Labeled key/value pairs; value charset is alnum + `_` + `-` only ([`redact.py:9–11`](skills/grader/scripts/redact.py#L9-L11)) |
| `email` | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` | Email addresses ([`redact.py:13`](skills/grader/scripts/redact.py#L13)) |

Replacement tokens: `[REDACTED_SECRET]` for secrets, `[REDACTED_EMAIL]` for emails ([`redact.py:21–25`](skills/grader/scripts/redact.py#L21-L25)).

### Test corpus coverage

The fixture `skills/grader/fixtures/secrets/corpus.jsonl` exercises:

- Anthropic keys (`sk-ant-api03-…`, `sk-ant-admin01-…`) — lines 1–2
- OpenAI keys (`sk-…`) — lines 3–4
- GitHub classic PATs (`ghp_…`) — lines 5–6
- Generic bearer (`api_key:`, `token =`, `secret:`) — lines 7–9
- Emails — lines 10–11
- Mixed — line 12
- Negative controls (normal prompt text) — lines 13–14

Recall gate: `tests/test_redact.py` requires ≥99% recall on `expect_redacted: true` rows ([`tests/test_redact.py:17–31`](tests/test_redact.py#L17-L31)).

Redaction fidelity gate (Phase 5): cues must survive redaction at ≥85% rate; tested via `skills/grader/scripts/redaction_fidelity.py` ([`redaction_fidelity.py:11`](skills/grader/scripts/redaction_fidelity.py#L11), [`tests/test_redaction_fidelity.py`](tests/test_redaction_fidelity.py)).

---

## 2. Coolify API token format (primary source)

**Official docs:** [Coolify Authorization](https://coolify.io/docs/api-reference/authorization)

Coolify uses Laravel Sanctum bearer tokens:

- Format: `{numeric_id}|{secret_hash}` — both parts required ([Coolify docs — "Create an API Token"](https://coolify.io/docs/api-reference/authorization))
- Example from docs: `67|abcthisisa123dummytoken` ([Coolify docs — Example Data](https://coolify.io/docs/api-reference/authorization))
- Older docs sample: `3|WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7` ([coolify-docs `authorization.md`](https://github.com/coollabsio/coolify-docs/blob/b38dd58e/docs/api-reference/authorization.md))
- Transport: `Authorization: Bearer {full_token}` ([Coolify docs — "Make API Requests"](https://coolify.io/docs/api-reference/authorization))
- Terraform provider confirms numeric prefix is mandatory: `42|abc123def456...` ([Terraform Coolify provider — Common Errors](https://registry.terraform.io/providers/coolify-terraform/coolify/latest/docs/guides/common-errors))

### Why Coolify tokens slip past

1. No `\d+\|` prefix rule exists in `_SECRET_PATTERNS`.
2. `generic_bearer` value class `[A-Za-z0-9_\-]{16,}` **excludes `|`**, so even `token = 67|abcthisisa123dummytoken` fails to match.
3. `Authorization: Bearer 67|…` has no `api_key`/`token`/`secret` label before `:=` — `Bearer` is not in the pattern.

**Verified leak (local run against `redact.py`):**

```
coolify: Authorization: Bearer 67|abcthisisa123dummytoken  → leaked=True
coolify2: COOLIFY_TOKEN=8|WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7  → leaked=True
token_pipe: token = 67|abcthisisa123dummytoken  → leaked=True
```

---

## 3. Residual gaps — high-likelihood formats in agent logs

Tested 2026-07-24 by importing `redact.redact_text` with representative samples. All below **leaked unchanged** unless noted.

### 3.1 Coolify / Laravel Sanctum tokens

| Example | Leaks? | Why |
|---------|--------|-----|
| `67\|abcthisisa123dummytoken` | Yes | No Sanctum rule; `\|` excluded from generic value |
| `8\|WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7` | Yes | Same |

**Likelihood in agent logs:** High — Coolify deploy automation, MCP server setup, curl examples in agent output.

### 3.2 GitHub tokens beyond `ghp_`

GitHub documents six prefix families ([GitHub token formats](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)):

| Prefix | Type | Caught? |
|--------|------|---------|
| `ghp_` | Classic PAT | Yes ([`redact.py:8`](skills/grader/scripts/redact.py#L8)) |
| `github_pat_` | Fine-grained PAT | **No** |
| `gho_` | OAuth access token | **No** |
| `ghu_` | GitHub App user token | **No** |
| `ghs_` | GitHub App installation token | **No** |
| `ghr_` | GitHub App refresh token | **No** |

**Likelihood:** High — agents routinely echo `gh` CLI output, Actions tokens, App installation tokens.

### 3.3 `Authorization: Bearer` without label keyword

| Example | Leaks? |
|---------|--------|
| `Authorization: Bearer eyJhbGciOiJIUzI1NiJ9…` | Yes |
| `Bearer 67\|abcthisisa123dummytoken` | Yes |

REST APIs commonly use `Authorization: Bearer` ([GitHub REST auth](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)); current `generic_bearer` only keys off `api_key`/`token`/`secret` with `:=`, not `Bearer`.

### 3.4 JWTs (`eyJ…`)

| Example | Leaks? |
|---------|--------|
| `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U` | Yes |

JWTs use base64url segments separated by `.` — excluded from `generic_bearer` charset. GitHub explicitly notes JWT auth requires `Authorization: Bearer` ([GitHub REST auth](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)).

### 3.5 PEM private keys

| Example | Leaks? |
|---------|--------|
| `-----BEGIN RSA PRIVATE KEY-----` | Yes |
| `-----BEGIN OPENSSH PRIVATE KEY-----` | Yes (same class) |

**Likelihood:** Medium-high — agents paste keys during SSH/deploy debugging.

### 3.6 Database / service connection URLs

| Example | Leaks? |
|---------|--------|
| `postgres://user:secretpass123@localhost:5432/db` | Yes |
| `mongodb+srv://user:pass@cluster.mongodb.net/db` | Yes (same class) |

URL scheme + embedded `user:password@` not covered. **Likelihood:** High in infra/DevOps agent sessions.

### 3.7 Cloud and SaaS API key prefixes

| Vendor | Prefix / pattern | Caught? | Primary reference |
|--------|-------------------|---------|-------------------|
| AWS access key ID | `AKIA[0-9A-Z]{16}` | **No** | [AWS access key format](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) |
| Google API key | `AIzaSy` + 33 chars | **No** | [Google API key docs](https://cloud.google.com/docs/authentication/api-keys) |
| Slack bot token | `xoxb-` | **No** | [Slack token types](https://api.slack.com/authentication/token-types) |
| Stripe secret key | `sk_live_` / `sk_test_` | **No** | [Stripe API keys](https://docs.stripe.com/keys) |
| npm access token | `npm_` | **No** | [npm access tokens](https://docs.npmjs.com/creating-and-viewing-access-tokens) |
| GitLab PAT | `glpat-` | **No** | [GitLab PAT docs](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) |

**Note on Stripe:** `sk_live_…` does **not** match `openai_key` (`sk-[A-Za-z0-9]{20,}`) because Stripe uses underscore (`sk_live_`) not hyphen-only continuation.

**Note on OpenAI project keys:** `sk-proj-…` does **not** match `openai_key` because the 20+ alnum run is interrupted by hyphens in `sk-proj-…` (verified leak).

### 3.8 `generic_bearer` structural limitations

Even labeled secrets leak when the value contains characters outside `[A-Za-z0-9_\-]`:

| Character | Breaks generic_bearer? | Appears in |
|-----------|---------------------|------------|
| `\|` | Yes | Coolify/Sanctum |
| `.` | Yes | JWTs, npm tokens (`npm_…`), some base64 |
| `/` | Yes | Base64, PEM (if ever labeled) |
| `+` | Yes | Base64 |
| `@` | Yes | Rare in values but common in URLs when mis-labeled |

---

## 4. Proposed detection rules

Rules ordered by expected recall vs. false-positive tradeoff. All should emit `[REDACTED_SECRET]` and a distinct `redaction_flags` label for observability.

### 4.1 Coolify / Laravel Sanctum token

```regex
(?<!\d)\d{1,10}\|[A-Za-z0-9]{20,}
```

| Aspect | Detail |
|--------|--------|
| Rationale | Matches official `ID\|HASH` format ([Coolify docs](https://coolify.io/docs/api-reference/authorization)) |
| FP risk | **Low–medium** — `\d+\|` + 20+ alnum is uncommon in prose; watch version strings like `HTTP/2` (no long hash after pipe) |
| Mitigation | Require ≥20 chars after `\|`; optional context boost when preceded by `Bearer` or `COOLIFY` |

### 4.2 `Authorization: Bearer` opaque token

```regex
(?i)Authorization:\s*Bearer\s+([A-Za-z0-9._\-|+/=]{20,})
```

| Aspect | Detail |
|--------|--------|
| Rationale | Catches Coolify, JWT, and opaque tokens in standard header form ([Coolify](https://coolify.io/docs/api-reference/authorization), [GitHub REST](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)) |
| FP risk | **Low** in agent transcripts — full `Authorization:` header rare in user prompts |
| Mitigation | Anchor on `Authorization:` prefix; don't match bare `Bearer` in isolation |

### 4.3 GitHub extended token prefixes

```regex
gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}
```

| Aspect | Detail |
|--------|--------|
| Rationale | Covers all six GitHub prefix families ([GitHub token formats](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)) |
| FP risk | **Very low** — prefixes are GitHub-specific |
| Mitigation | None needed beyond minimum length |

### 4.4 JWT (three base64url segments)

```regex
eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
```

| Aspect | Detail |
|--------|--------|
| Rationale | Standard JWT layout; header always base64url-json starting with `eyJ` |
| FP risk | **Low–medium** — long base64-like strings rare in prompts; could match crafted test data |
| Mitigation | Require `eyJ` header (JWT JSON `{"` → `eyJ`); min segment lengths |

### 4.5 PEM private key blocks

```regex
-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----
```

| Aspect | Detail |
|--------|--------|
| Rationale | Standard PEM envelope |
| FP risk | **Very low** |
| Mitigation | Multiline match only when BEGIN/END present |

### 4.6 Database URL credentials

```regex
(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:@]{1,64}:[^\s@]{8,}@[^\s/]+
```

| Aspect | Detail |
|--------|--------|
| Rationale | Catches `scheme://user:password@host` — common leak in deploy/debug output |
| FP risk | **Medium** — `redis://localhost:6379` without password is safe; rule requires `:password@` |
| Mitigation | Password segment min length 8; require `@` after password |

### 4.7 Vendor prefix rules (single-regex bundle)

```regex
(?:AKIA[0-9A-Z]{16}|AIzaSy[A-Za-z0-9_-]{33}|xox[baprs]-[A-Za-z0-9-]{10,}|sk_(?:live|test)_[A-Za-z0-9]{20,}|npm_[A-Za-z0-9]{36}|glpat-[A-Za-z0-9_-]{20,})
```

| Aspect | Detail |
|--------|--------|
| Rationale | High-signal vendor prefixes ([AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html), [Google](https://cloud.google.com/docs/authentication/api-keys), [Slack](https://api.slack.com/authentication/token-types), [Stripe](https://docs.stripe.com/keys), [npm](https://docs.npmjs.com/creating-and-viewing-access-tokens), [GitLab](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)) |
| FP risk | **Very low** per prefix |
| Mitigation | Prefix-anchored; extend list rather than broadening charset |

### 4.8 Harden `generic_bearer` value charset

```regex
(?i)(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'"]{16,}
```

| Aspect | Detail |
|--------|--------|
| Rationale | Allow any non-whitespace value ≥16 chars when explicitly labeled |
| FP risk | **Medium** — `password: hunter2` in examples; `token: abcdefghijklmnop` in docs |
| Mitigation | Keep label requirement; consider excluding values that are dictionary words or match `[a-z]+` only; add `password`/`passwd` labels |

---

## 5. False-positive risk summary

| Rule | FP risk | Main collision source |
|------|---------|----------------------|
| Sanctum `\d+\|…` | Low–medium | Rare pipe-delimited IDs in logs |
| `Authorization: Bearer` | Low | Almost always a real header |
| GitHub extended prefixes | Very low | Vendor-specific |
| JWT | Low–medium | Long random test strings |
| PEM blocks | Very low | Distinct delimiters |
| DB URLs | Medium | Tutorial connection strings in docs |
| Vendor prefixes | Very low | Prefix-anchored |
| Broadened generic_bearer | Medium | Labeled examples in instructional text |

**Fidelity constraint:** New rules must preserve cue tokens for grading attribution ([`redaction_fidelity.py:14–17`](skills/grader/scripts/redaction_fidelity.py#L14-L17)). Prefer surgical prefix/context rules over blanket high-entropy matchers.

---

## 6. Recommended implementation order

1. **Sanctum / Coolify** — ticket motivator; high signal, low FP.
2. **GitHub extended prefixes** — trivial extension of existing `github_pat` rule.
3. **`Authorization: Bearer`** — catches Coolify + JWT + opaque tokens in one rule.
4. **Vendor prefix bundle** — AWS, Slack, Stripe, npm, GitLab, Google.
5. **PEM blocks** — high severity when present.
6. **DB URL credentials** — high recall in DevOps sessions; tune password min-length.
7. **Broaden `generic_bearer`** — last; highest FP surface.

---

## 7. Top 5 gaps (quick reference)

| Rank | Gap | Example | Root cause |
|------|-----|---------|------------|
| 1 | Coolify / Sanctum tokens | `8\|WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7` | No `\d+\|` rule; `\|` excluded from generic value ([`redact.py:9–11`](skills/grader/scripts/redact.py#L9-L11)) |
| 2 | `Authorization: Bearer` headers | `Bearer 67\|abcthisisa123dummytoken` | No Bearer-header rule ([`redact.py:9–11`](skills/grader/scripts/redact.py#L9-L11)) |
| 3 | GitHub non-`ghp_` tokens | `github_pat_11ABC…`, `gho_…`, `ghs_…` | Only `ghp_` covered ([`redact.py:8`](skills/grader/scripts/redact.py#L8); [GitHub formats](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)) |
| 4 | JWTs | `eyJhbGciOiJIUzI1NiIs…` | `.` excluded from generic value; no JWT rule |
| 5 | DB connection URLs | `postgres://user:secretpass123@host/db` | No URL-credential rule |

---

## Appendix: empirical leak matrix

Run: `python -c "…"` against `skills/grader/scripts/redact.py` on branch `research/residual-secret-redaction`, 2026-07-24.

| Sample ID | Leaked |
|-----------|--------|
| coolify Bearer | Yes |
| coolify env var | Yes |
| github_pat_fg | Yes |
| github_gho | Yes |
| slack xoxb | Yes |
| stripe sk_live | Yes |
| aws AKIA | Yes |
| jwt | Yes |
| pem private key | Yes |
| postgres URL | Yes |
| google AIzaSy | Yes |
| npm token | Yes |
| gitlab glpat | Yes |
| bearer JWT | Yes |
| token = pipe value | Yes |
| api_key: pipe value | Yes |
| openai sk-proj | Yes |
