from __future__ import annotations

import re

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9-]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_pat_ext", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("github_oauth", re.compile(r"gho_[A-Za-z0-9]{20,}")),
    ("github_user", re.compile(r"ghu_[A-Za-z0-9]{20,}")),
    ("github_app", re.compile(r"ghs_[A-Za-z0-9]{20,}")),
    ("github_refresh", re.compile(r"ghr_[A-Za-z0-9]{20,}")),
    ("sanctum_token", re.compile(r"(?<!\d)\d{1,10}\|[A-Za-z0-9]{20,}")),
    (
        "authorization_bearer",
        re.compile(r"(?i)Authorization:\s*Bearer\s+[A-Za-z0-9._\-|+/=]{20,}"),
    ),
    (
        "jwt",
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
    ),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("google_api_key", re.compile(r"AIzaSy[A-Za-z0-9_-]{33}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("stripe_key", re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{20,}")),
    ("npm_token", re.compile(r"npm_[A-Za-z0-9]{36}")),
    ("gitlab_pat", re.compile(r"glpat-[A-Za-z0-9_-]{20,}")),
    (
        "pem_private_key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            r"[\s\S]*?"
            r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
    (
        "db_url_credentials",
        re.compile(
            r"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://"
            r"[^\s:@]{1,64}:[^\s@]{8,}@[^\s/]+"
        ),
    ),
    ("generic_bearer", re.compile(
        r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"
    )),
]
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def redact_text(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(out):
            out = pattern.sub("[REDACTED_SECRET]", out)
            if label not in notes:
                notes.append(label)
    if _EMAIL.search(out):
        out = _EMAIL.sub("[REDACTED_EMAIL]", out)
        if "email" not in notes:
            notes.append("email")
    return out, notes
