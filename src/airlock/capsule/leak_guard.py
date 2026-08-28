"""Final fail-closed guard for every externally visible payload."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from airlock.detectors import Sensitivity, detect_all
from airlock.errors import LeakageGuardError

_DIGITS_RE = re.compile(r"\D+")

# Residual checks intentionally do not import or reuse production detector
# regexes. One detector regression must not also disable the release/Qoder gate.
_OUTPUT_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?P<label>(?:(?:RSA|EC|DSA|OPENSSH|ENCRYPTED) )?PRIVATE KEY)-----"
    r"[\s\S]*?-----END (?P=label)-----"
)
_OUTPUT_BEARER = re.compile(r"(?i)\bbearer[ \t]+(?P<value>[A-Za-z0-9._~+/=-]{12,})")
_OUTPUT_JWT = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
    r"(?![A-Za-z0-9_-])"
)
_OUTPUT_AWS_KEY_ID = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
_OUTPUT_PREFIXED_KEY = re.compile(
    r"(?<![A-Za-z0-9_-])sk-(?:test-)?[A-Za-z0-9][A-Za-z0-9_-]{11,}"
    r"(?![A-Za-z0-9_-])"
)
_OUTPUT_DATABASE_URL = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|"
    r"amqp|mssql)://[^\s\"'<>]+"
)
_OUTPUT_LABELED_TOKEN = re.compile(
    r"(?<![A-Z0-9_-])"
    r"(?P<value>(?P<namespace>(?:[A-Z][A-Z0-9]*[_-])+?)"
    r"(?P<label>SECRET|PASSWORD|TOKEN)[_-]"
    r"(?P<suffix>(?=[A-Z0-9]{5,}(?![A-Z0-9_-]))"
    r"(?=[A-Z0-9]*\d[A-Z])[A-Z0-9]{5,}))"
    r"(?![A-Z0-9_-])"
)
_OUTPUT_SYMBOLIC_STATUS_SUFFIX = re.compile(
    r"E?\d{3,5}(?:BADREQUEST|CONFLICT|DENIED|ERROR|FAILED|FORBIDDEN|GONE|"
    r"NOTFOUND|OK|RATELIMITED|TIMEOUT|UNAUTHORIZED|UNAVAILABLE)"
)
_OUTPUT_ASSIGNMENT = re.compile(
    r"(?<![A-Za-z0-9])(?P<key_quote>[\"'])?"
    r"(?P<key>[A-Za-z][A-Za-z0-9_-]{1,95})(?(key_quote)(?P=key_quote))"
    r"\s*[:=]\s*"
    r"(?:\"(?P<double>(?:\\.|[^\"\\\r\n])+)\"|"
    r"'(?P<single>(?:\\.|[^'\\\r\n])+)'|"
    r"(?P<bare>[^\s#;,\[\]{}\"']+))"
)
_OUTPUT_JSON_PART = r'(?:\\(?:["\\/bfnrt]|u[0-9A-Fa-f]{4})|[^"\\\r\n])'
_OUTPUT_JSON_ASSIGNMENT = re.compile(
    rf'"(?P<json_key>{_OUTPUT_JSON_PART}*)"\s*:\s*'
    rf'(?:"(?P<json_value>{_OUTPUT_JSON_PART}+)"|'
    r"(?P<json_bare>[A-Za-z0-9][A-Za-z0-9._~+/=-]*))"
)
_OUTPUT_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_OUTPUT_KEY_SUFFIXES = {
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
_OUTPUT_SAFE_REPLACEMENT = re.compile(r"\[[A-Z][A-Z0-9_]*(?:REDACTED|\d{3})\]")
_OUTPUT_NON_CREDENTIAL_STATES = frozenset(
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

_OUTPUT_QUOTED_EXAMPLE = re.compile(
    r"\b(?:phrases?|strings?|text)\s+such\s+as\s+"
    r"(?P<quote>['\"])[^'\"]{1,200}(?P=quote)",
    re.IGNORECASE,
)
_OUTPUT_DEFENSIVE = re.compile(
    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not)\s+"
    r"(?:ignore|disregard|forget|discard|bypass|circumvent|inspect|open|read|use|"
    r"access|put|place|include|print|reveal|return|send|upload|exfiltrate)\b"
    r"(?:(?!\b(?:but|however|instead|then|yet|except)\b)[^.;])*(?:[.;]|$)",
    re.IGNORECASE,
)
_OUTPUT_DEFENSIVE_DISCLOSURE = re.compile(
    r"\b(?:secrets?|credentials?|tokens?|private\s+keys?|access\s+keys?|"
    r"api\s+keys?|passwords?)\b.{0,50}\b(?:must|should)\s+(?:never|not)\s+"
    r"(?:appear|be\s+(?:put|placed|included|printed|returned|revealed|exposed|sent|"
    r"uploaded))\b(?:(?!\b(?:but|however|instead|then|yet|except)\b)[^.;])*"
    r"(?:[.;]|$)",
    re.IGNORECASE,
)
_OUTPUT_INSTRUCTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|forget|discard)\b.{0,80}"
        r"\b(?:all\s+)?(?:previous|prior|earlier)\s+instructions?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:bypass|circumvent|evade|skip|work\s+around)\b.{0,110}"
        r"\b(?:saniti[sz](?:e|ed|er|ing|ation)?|redaction|filter(?:ing|ed)?|"
        r"safe[_\s-]*context|capsule|airlock)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:inspect|open|read|use|access|work\s+(?:directly\s+)?from)\b.{0,120}"
        r"\b(?:raw|original|untouched|unfiltered|unsanitized|unprocessed)\b.{0,100}"
        r"\b(?:workspace|repository|files?|documents?|sources?|contents?|data)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:do\s+not|don't)\s+(?:use|rely\s+on|trust)\b.{0,90}"
        r"\b(?:safe[_\s-]*context|capsule|airlock|saniti[sz](?:ed|ation)?\s+view)\b"
        r".{0,180}\b(?:raw|original|untouched|unfiltered|unsanitized|unprocessed)\b",
        re.IGNORECASE,
    ),
)


def _group_span(match: re.Match[str], *names: str) -> tuple[int, int]:
    for name in names:
        if match.groupdict().get(name) is not None:
            return match.span(name)
    return match.span()


def _output_key_tokens(key: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", key)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,95}", normalized):
        return ()
    pieces: list[str] = []
    for segment in re.split(r"[_-]+", normalized):
        pieces.extend(part.casefold() for part in _OUTPUT_CAMEL_BOUNDARY.split(segment) if part)
    return tuple(pieces)


def _output_key_kind(key: str) -> str | None:
    tokens = _output_key_tokens(key)
    if not tokens:
        return None
    if tokens[-1] in {"password", "passwd", "pwd"}:
        return "password"
    if tokens[-1] == "token" or any(
        len(tokens) >= len(suffix) and tokens[-len(suffix) :] == suffix
        for suffix in _OUTPUT_KEY_SUFFIXES
    ):
        return "api_key"
    return None


def _decode_output_json_string(value: str) -> str | None:
    try:
        decoded = json.loads(f'"{value}"')
    except (json.JSONDecodeError, RecursionError, UnicodeError):
        return None
    return decoded if isinstance(decoded, str) else None


def _output_value_is_sensitive(kind: str, value: str, *, json_string: bool = False) -> bool:
    decoded = _decode_output_json_string(value) if json_string else value
    if decoded is None or _OUTPUT_SAFE_REPLACEMENT.fullmatch(decoded):
        return False
    stripped = decoded.strip()
    if len(stripped) >= 2 and stripped[0] == "<" and stripped[-1] == ">":
        stripped = stripped[1:-1].strip()
    if stripped.casefold() in _OUTPUT_NON_CREDENTIAL_STATES:
        return False
    return bool(decoded) and (kind == "password" or len(decoded) >= 8)


def _output_labeled_marker_is_sensitive(match: re.Match[str]) -> bool:
    suffix = match.group("suffix")
    if _OUTPUT_SYMBOLIC_STATUS_SUFFIX.fullmatch(suffix):
        return False
    transitions = sum(
        left.isdigit() != right.isdigit() for left, right in zip(suffix, suffix[1:], strict=False)
    )
    minimum = 3 if match.group("label") == "TOKEN" else 2
    return transitions >= minimum


def _independent_sensitive_intervals(text: str) -> set[tuple[int, int]]:
    intervals: set[tuple[int, int]] = set()
    for pattern in (
        _OUTPUT_PRIVATE_KEY,
        _OUTPUT_JWT,
        _OUTPUT_AWS_KEY_ID,
        _OUTPUT_PREFIXED_KEY,
        _OUTPUT_DATABASE_URL,
    ):
        intervals.update(match.span() for match in pattern.finditer(text))
    intervals.update(match.span("value") for match in _OUTPUT_BEARER.finditer(text))
    intervals.update(
        match.span("value")
        for match in _OUTPUT_LABELED_TOKEN.finditer(text)
        if _output_labeled_marker_is_sensitive(match)
    )

    for match in _OUTPUT_ASSIGNMENT.finditer(text):
        kind = _output_key_kind(match.group("key"))
        if kind is None:
            continue
        start, end = _group_span(match, "double", "single", "bare")
        candidate = text[start:end]
        if match.group("double") is not None:
            candidate = _decode_output_json_string(candidate) or candidate
        if _output_value_is_sensitive(kind, candidate):
            intervals.add((start, end))

    for match in _OUTPUT_JSON_ASSIGNMENT.finditer(text):
        key = _decode_output_json_string(match.group("json_key"))
        kind = _output_key_kind(key) if key is not None else None
        if kind is None:
            continue
        start, end = _group_span(match, "json_value", "json_bare")
        if _output_value_is_sensitive(
            kind,
            text[start:end],
            json_string=match.group("json_value") is not None,
        ):
            intervals.add((start, end))
    return intervals


def _independent_instruction_intervals(text: str) -> set[tuple[int, int]]:
    if not text:
        return set()
    projected = re.sub(r"[\t\r\n ]+", " ", unicodedata.normalize("NFKC", text)).strip()
    projected = _OUTPUT_QUOTED_EXAMPLE.sub(lambda match: " " * len(match.group(0)), projected)
    projected = _OUTPUT_DEFENSIVE_DISCLOSURE.sub(lambda match: " " * len(match.group(0)), projected)
    projected = _OUTPUT_DEFENSIVE.sub(lambda match: " " * len(match.group(0)), projected)
    if any(pattern.search(projected) for pattern in _OUTPUT_INSTRUCTION_PATTERNS):
        return {(0, len(text))}
    return set()


@dataclass(frozen=True, slots=True)
class PayloadInspection:
    """Value-free result of independently inspecting one public payload."""

    raw_sensitive_spans_forwarded: int
    untrusted_instruction_spans_forwarded: int
    registered_value_leaks: int


def _variants(value: str) -> tuple[str, ...]:
    variants = {value.casefold()}
    digits = _DIGITS_RE.sub("", value)
    if len(digits) >= 7:
        variants.add(digits)
    return tuple(item for item in variants if len(item) >= 4)


def find_sensitive_leaks(payloads: Iterable[str], sensitive_values: Iterable[str]) -> int:
    """Count distinct source values that remain in any public payload."""

    folded_payloads = tuple(payload.casefold() for payload in payloads)
    digit_payloads = tuple(_DIGITS_RE.sub("", payload) for payload in payloads)
    leaked = 0
    for value in set(sensitive_values):
        matched = False
        for variant in _variants(value):
            haystacks = digit_payloads if variant.isdigit() else folded_payloads
            if any(variant in payload for payload in haystacks):
                matched = True
                break
        leaked += int(matched)
    return leaked


def _string_leaves(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _string_leaves(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _string_leaves(item)


def _literal_intervals(text: str, value: str) -> list[tuple[int, int]]:
    folded_text = text.casefold()
    folded_value = value.casefold()
    if len(folded_value) < 4:
        return []
    intervals: list[tuple[int, int]] = []
    cursor = 0
    while (start := folded_text.find(folded_value, cursor)) >= 0:
        end = start + len(folded_value)
        intervals.append((start, end))
        cursor = end
    return intervals


def _merged_interval_count(intervals: Iterable[tuple[int, int, int]]) -> int:
    ordered = sorted(intervals)
    if not ordered:
        return 0
    count = 0
    active_leaf = -1
    active_end = -1
    for leaf, start, end in ordered:
        if leaf != active_leaf or start >= active_end:
            count += 1
            active_leaf = leaf
            active_end = end
        else:
            active_end = max(active_end, end)
    return count


def inspect_public_payload(
    payload: Any,
    sensitive_values: Iterable[str] = (),
) -> PayloadInspection:
    """Re-scan final structured output instead of trusting upstream findings.

    String leaves are inspected before JSON escaping, so a quoted JSON credential
    embedded inside a fact remains visible to the independent post-condition.
    """

    texts = tuple(_string_leaves(payload))
    protected = tuple(set(sensitive_values))
    sensitive_intervals: set[tuple[int, int, int]] = set()
    instruction_intervals: set[tuple[int, int, int]] = set()

    for leaf, text in enumerate(texts):
        for finding in detect_all(text, "<public-output>"):
            identity = (leaf, finding.span.start, finding.span.end)
            if finding.sensitivity in {Sensitivity.SECRET, Sensitivity.PII}:
                sensitive_intervals.add(identity)
            elif finding.sensitivity is Sensitivity.UNTRUSTED_INSTRUCTION:
                instruction_intervals.add(identity)
        sensitive_intervals.update(
            (leaf, start, end) for start, end in _independent_sensitive_intervals(text)
        )
        instruction_intervals.update(
            (leaf, start, end) for start, end in _independent_instruction_intervals(text)
        )

    normalized_only = 0
    for value in protected:
        direct = False
        for leaf, text in enumerate(texts):
            for start, end in _literal_intervals(text, value):
                sensitive_intervals.add((leaf, start, end))
                direct = True
        if direct:
            continue
        digits = _DIGITS_RE.sub("", value)
        if len(digits) >= 7 and any(digits in _DIGITS_RE.sub("", text) for text in texts):
            normalized_only += 1

    return PayloadInspection(
        raw_sensitive_spans_forwarded=(
            _merged_interval_count(sensitive_intervals) + normalized_only
        ),
        untrusted_instruction_spans_forwarded=_merged_interval_count(instruction_intervals),
        registered_value_leaks=find_sensitive_leaks(texts, protected),
    )


def enforce_public_payload_is_safe(
    payload: Any,
    sensitive_values: Iterable[str] = (),
) -> PayloadInspection:
    """Fail closed if final output contains sensitive or executable raw content."""

    inspection = inspect_public_payload(payload, sensitive_values)
    if (
        inspection.raw_sensitive_spans_forwarded
        or inspection.untrusted_instruction_spans_forwarded
        or inspection.registered_value_leaks
    ):
        raise LeakageGuardError()
    return inspection


def enforce_no_sensitive_leaks(payloads: Iterable[str], sensitive_values: Iterable[str]) -> None:
    if find_sensitive_leaks(payloads, sensitive_values):
        raise LeakageGuardError()
