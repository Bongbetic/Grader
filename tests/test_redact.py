# tests/test_redact.py
import json
from pathlib import Path

from redact import redact_text

CORPUS = Path("skills/grader/fixtures/secrets/corpus.jsonl")


def _corpus_text(row: dict) -> str:
    if "text_parts" in row:
        return "".join(row["text_parts"])
    return row["text"]


def test_redacts_email():
    out, notes = redact_text("contact me at alice@example.com please")
    assert "alice@example.com" not in out
    assert "[REDACTED_EMAIL]" in out
    assert "email" in notes


def test_corpus_recall():
    lines = CORPUS.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 10
    hits = 0
    expected = 0
    for line in lines:
        row = json.loads(line)
        if not row["expect_redacted"]:
            continue
        expected += 1
        text = _corpus_text(row)
        cleaned, notes = redact_text(text)
        if notes and cleaned != text:
            hits += 1
    assert expected > 0
    assert hits / expected >= 0.99


def test_corpus_negative_controls_untouched():
    for line in CORPUS.read_text(encoding="utf-8").strip().splitlines():
        row = json.loads(line)
        if row["expect_redacted"]:
            continue
        text = _corpus_text(row)
        cleaned, notes = redact_text(text)
        assert cleaned == text
        assert notes == []


def test_redacts_sanctum_coolify_token():
    raw = "COOLIFY_TOKEN=8|WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7"
    out, notes = redact_text(raw)
    assert "WaobqX9tJQshKPuQFHsyApxuOOggg4wOfvGc9xa233c376d7" not in out
    assert "[REDACTED_SECRET]" in out
    assert "sanctum_token" in notes


def test_redacts_github_extended_tokens():
    samples = [
        ("github_pat_11ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd", "github_pat_ext"),
        ("gho_abcdefghijklmnopqrstuvwxyz0123456789", "github_oauth"),
        ("ghs_abcdefghijklmnopqrstuvwxyz0123456789", "github_app"),
    ]
    for raw, label in samples:
        out, notes = redact_text(f"auth {raw}")
        assert raw not in out
        assert "[REDACTED_SECRET]" in out
        assert label in notes


def test_redacts_authorization_bearer():
    raw = (
        "Authorization: Bearer "
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    out, notes = redact_text(raw)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in out
    assert "[REDACTED_SECRET]" in out
    assert "authorization_bearer" in notes


def test_redacts_bare_jwt():
    raw = (
        "token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    out, notes = redact_text(raw)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in out
    assert "[REDACTED_SECRET]" in out
    assert "jwt" in notes


def test_redacts_vendor_prefixes():
    samples = [
        ("AKIAAAAAAAAAAAAAAAAA", "aws_access_key"),
        ("AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456", "google_api_key"),
        ("xoxb-1234567890-abcdefghij", "slack_token"),
        ("sk_" + "live_abcdefghijklmnopqrstuvwxyz12", "stripe_key"),
        ("npm_abcdefghijklmnopqrstuvwxyz0123456789", "npm_token"),
        ("glpat-abcdefghijklmnopqrstuvwxyz01", "gitlab_pat"),
    ]
    for raw, label in samples:
        out, notes = redact_text(f"key {raw}")
        assert raw not in out
        assert "[REDACTED_SECRET]" in out
        assert label in notes


def test_redacts_pem_private_key():
    raw = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZX6W+\n"
        "-----END RSA PRIVATE KEY-----"
    )
    out, notes = redact_text(raw)
    assert "BEGIN RSA PRIVATE KEY" not in out
    assert "[REDACTED_SECRET]" in out
    assert "pem_private_key" in notes


def test_redacts_db_url_credentials():
    raw = "postgres://user:secretpass123@localhost:5432/db"
    out, notes = redact_text(raw)
    assert "secretpass123" not in out
    assert "[REDACTED_SECRET]" in out
    assert "db_url_credentials" in notes


def test_redacts_openai_sk_proj():
    raw = "here is my key sk-proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF"
    out, notes = redact_text(raw)
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF" not in out
    assert "[REDACTED_SECRET]" in out
    assert "openai_key" in notes
