"""High-precision deterministic Secret detectors."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass

from .models import Action, InternalFinding, Sensitivity, Span, line_number
from .overlap import resolve_sensitive_overlaps


@dataclass(frozen=True, slots=True)
class _SecretMatch:
    finding_type: str
    start: int
    end: int


_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?P<label>(?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY)-----"
    r"[\s\S]*?"
    r"-----END (?P=label)-----"
)

_DATABASE_URL = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|"
    r"amqp|mssql)://[^\s\"'<>]+"
)

_CONNECTION_STRING = re.compile(
    r"(?im)(?=[^\r\n]{0,2048}\b(?:password|pwd)\s*=)"
    r"\b(?:driver|server|data\s+source|host)\s*=[^\r\n]{1,2048}"
)

_BEARER_TOKEN = re.compile(r"(?i)\bbearer[ \t]+(?P<value>[A-Za-z0-9._~+/=-]{12,})")

_JWT = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
    r"(?![A-Za-z0-9_-])"
)

_AWS_ACCESS_KEY = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")

_PREFIXED_API_KEY = re.compile(
    r"(?<![A-Za-z0-9_-])sk-(?:test-)?[A-Za-z0-9][A-Za-z0-9_-]{11,}"
    r"(?![A-Za-z0-9_-])"
)

_ASSIGNED_API_KEY = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\b"
    r"\s*[:=]\s*[\"']?"
    r"(?P<value>[A-Za-z0-9][A-Za-z0-9._~+/=-]{7,})"
)

_PASSWORD_ASSIGNMENT = re.compile(
    r"(?i)\b(?:(?:database|db)[_-]?)?(?:password|passwd|pwd)\b\s*[:=]\s*"
    r"(?:\"(?P<double>[^\"\r\n]+)\"|"
    r"'(?P<single>[^'\r\n]+)'|"
    r"(?P<bare>[^\s#;,\[\]]+))"
)


def _group_span(match: re.Match[str], *names: str) -> tuple[int, int]:
    for name in names:
        if match.groupdict().get(name) is not None:
            return match.span(name)
    return match.span()


def _iter_secret_matches(text: str) -> Iterator[_SecretMatch]:
    for match in _PRIVATE_KEY.finditer(text):
        yield _SecretMatch("PRIVATE_KEY", *match.span())

    for match in _DATABASE_URL.finditer(text):
        start, end = match.span()
        while end > start and text[end - 1] in ".,;)]}":
            end -= 1
        if end > start:
            yield _SecretMatch("DATABASE_URL", start, end)

    for match in _CONNECTION_STRING.finditer(text):
        yield _SecretMatch("CONNECTION_STRING", *match.span())

    for match in _BEARER_TOKEN.finditer(text):
        yield _SecretMatch("BEARER_TOKEN", *_group_span(match, "value"))

    for match in _JWT.finditer(text):
        yield _SecretMatch("JWT", *match.span())

    for match in _AWS_ACCESS_KEY.finditer(text):
        yield _SecretMatch("AWS_ACCESS_KEY", *match.span())

    for match in _PREFIXED_API_KEY.finditer(text):
        yield _SecretMatch("API_KEY", *match.span())

    for match in _ASSIGNED_API_KEY.finditer(text):
        yield _SecretMatch("API_KEY", *_group_span(match, "value"))

    for match in _PASSWORD_ASSIGNMENT.finditer(text):
        yield _SecretMatch("PASSWORD", *_group_span(match, "double", "single", "bare"))


def detect_secrets(text: str, source: str = "<input>") -> list[InternalFinding]:
    """Detect and deterministically de-duplicate supported Secret classes.

    Findings contain offsets only; matched values are never stored on them.
    """

    findings = [
        InternalFinding(
            finding_type=match.finding_type,
            severity="critical",
            source=source,
            line=line_number(text, match.start),
            detector="regex",
            action=Action.REDACT,
            sensitivity=Sensitivity.SECRET,
            span=Span(match.start, match.end),
        )
        for match in _iter_secret_matches(text)
    ]
    return resolve_sensitive_overlaps(findings)
