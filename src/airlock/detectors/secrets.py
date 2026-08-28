"""High-precision deterministic Secret detectors."""

from __future__ import annotations

import json
import re
import unicodedata
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
    r"-----BEGIN (?P<label>(?:(?:RSA|EC|DSA|OPENSSH|ENCRYPTED) )?PRIVATE KEY)-----"
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

_ASSIGNED_CREDENTIAL = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?P<key_quote>[\"'])?"
    r"(?P<key>[A-Za-z][A-Za-z0-9_-]{1,95})"
    r"(?(key_quote)(?P=key_quote))"
    r"\s*[:=]\s*"
    r"(?:\"(?P<double>(?:\\.|[^\"\\\r\n])+)\"|"
    r"'(?P<single>(?:\\.|[^'\\\r\n])+)'|"
    r"(?P<bare>[^\s#;,\[\]{}\"']+))"
)

_JSON_STRING_PART = r'(?:\\(?:["\\/bfnrt]|u[0-9A-Fa-f]{4})|[^"\\\r\n])'
_JSON_ASSIGNED_CREDENTIAL = re.compile(
    rf'"(?P<json_key>{_JSON_STRING_PART}*)"\s*:\s*'
    rf'(?:"(?P<json_value>{_JSON_STRING_PART}+)"|'
    r"(?P<json_bare>[A-Za-z0-9][A-Za-z0-9._~+/=-]*))"
)

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

_API_KEY_SUFFIXES = {
    ("api", "key"),
    ("api", "token"),
    ("access", "key"),
    ("access", "token"),
    ("auth", "token"),
    ("authentication", "token"),
    ("refresh", "token"),
    ("id", "token"),
    ("client", "secret"),
    ("secret", "key"),
    ("secret", "access", "key"),
    ("access", "key", "secret"),
}

# Explicitly labelled, high-entropy-looking synthetic or generated tokens can
# occur in prose without assignment syntax.  Keep this deliberately narrow:
# an upper-case namespace must precede SECRET/PASSWORD/TOKEN, and the suffix must
# contain several letter/digit transitions. This catches values such as
# ``INTEGRATOR_SECRET_X91Q7`` without treating documentation identifiers or
# status-code constants as credential values.
_LABELED_SECRET_TOKEN = re.compile(
    r"(?<![A-Z0-9_-])"
    r"(?P<value>(?P<namespace>(?:[A-Z][A-Z0-9]*[_-])+?)"
    r"(?P<label>SECRET|PASSWORD|TOKEN)[_-]"
    r"(?P<suffix>(?=[A-Z0-9]{5,}(?![A-Z0-9_-]))"
    r"(?=[A-Z0-9]*\d[A-Z])[A-Z0-9]{5,}))"
    r"(?![A-Z0-9_-])"
)
_SYMBOLIC_STATUS_SUFFIX = re.compile(
    r"E?\d{3,5}(?:BADREQUEST|CONFLICT|DENIED|ERROR|FAILED|FORBIDDEN|GONE|"
    r"NOTFOUND|OK|RATELIMITED|TIMEOUT|UNAUTHORIZED|UNAVAILABLE)"
)

_SAFE_REPLACEMENT = re.compile(r"\[[A-Z][A-Z0-9_]*(?:REDACTED|\d{3})\]")
_NON_CREDENTIAL_STATES = frozenset(
    {
        "~",
        "absent",
        "disabled",
        "empty",
        "false",
        "masked",
        "missing",
        "na",
        "n/a",
        "nil",
        "none",
        "not configured",
        "not set",
        "not-configured",
        "not-set",
        "not_configured",
        "not_set",
        "notconfigured",
        "notset",
        "null",
        "off",
        "redacted",
        "removed",
        "unconfigured",
        "undefined",
        "unset",
        "unknown",
    }
)


def _credential_key_tokens(key: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", key)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,95}", normalized):
        return ()
    pieces: list[str] = []
    for segment in re.split(r"[_-]+", normalized):
        pieces.extend(part.casefold() for part in _CAMEL_BOUNDARY.split(segment) if part)
    return tuple(pieces)


def _credential_kind(key: str) -> str | None:
    tokens = _credential_key_tokens(key)
    if not tokens:
        return None
    if tokens[-1] in {"password", "passwd", "pwd"}:
        return "PASSWORD"
    if tokens[-1] == "token" or any(
        len(tokens) >= len(suffix) and tokens[-len(suffix) :] == suffix
        for suffix in _API_KEY_SUFFIXES
    ):
        return "API_KEY"
    return None


def _decode_json_string(value: str) -> str | None:
    try:
        decoded = json.loads(f'"{value}"')
    except (json.JSONDecodeError, RecursionError, UnicodeError):
        return None
    return decoded if isinstance(decoded, str) else None


def _is_noncredential_state(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == "<" and stripped[-1] == ">":
        stripped = stripped[1:-1].strip()
    return stripped.casefold() in _NON_CREDENTIAL_STATES


def _is_supported_value(finding_type: str, value: str, *, json_string: bool = False) -> bool:
    decoded = _decode_json_string(value) if json_string else value
    if decoded is None or _SAFE_REPLACEMENT.fullmatch(decoded) or _is_noncredential_state(decoded):
        return False
    if finding_type == "API_KEY":
        return len(decoded) >= 8
    return bool(decoded)


def _is_supported_labeled_marker(match: re.Match[str]) -> bool:
    suffix = match.group("suffix")
    if _SYMBOLIC_STATUS_SUFFIX.fullmatch(suffix):
        return False
    transitions = sum(
        left.isdigit() != right.isdigit() for left, right in zip(suffix, suffix[1:], strict=False)
    )
    minimum = 3 if match.group("label") == "TOKEN" else 2
    return transitions >= minimum


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

    for match in _ASSIGNED_CREDENTIAL.finditer(text):
        finding_type = _credential_kind(match.group("key"))
        if finding_type is None:
            continue
        start, end = _group_span(match, "double", "single", "bare")
        candidate = text[start:end]
        if match.group("double") is not None:
            candidate = _decode_json_string(candidate) or candidate
        if _is_supported_value(finding_type, candidate):
            yield _SecretMatch(finding_type, start, end)

    for match in _JSON_ASSIGNED_CREDENTIAL.finditer(text):
        decoded_key = _decode_json_string(match.group("json_key"))
        finding_type = _credential_kind(decoded_key) if decoded_key is not None else None
        if finding_type is None:
            continue
        start, end = _group_span(match, "json_value", "json_bare")
        if _is_supported_value(
            finding_type,
            text[start:end],
            json_string=match.group("json_value") is not None,
        ):
            yield _SecretMatch(finding_type, start, end)

    for match in _LABELED_SECRET_TOKEN.finditer(text):
        if not _is_supported_labeled_marker(match):
            continue
        finding_type = "PASSWORD" if match.group("label") == "PASSWORD" else "API_KEY"
        yield _SecretMatch(finding_type, *_group_span(match, "value"))


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
