"""Deterministic PII detectors for the v0.1 boundary."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterator
from dataclasses import dataclass

from .models import Action, InternalFinding, Sensitivity, Span, line_number
from .overlap import resolve_sensitive_overlaps


@dataclass(frozen=True, slots=True)
class _PiiMatch:
    finding_type: str
    start: int
    end: int
    severity: str


_EMAIL_ADDRESS = (
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}"
    r"(?![A-Za-z0-9-])"
)
_EMAIL = re.compile(r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~-])" + _EMAIL_ADDRESS)

# '=' and '+' are valid RFC 5322 local-part characters. Do not remove them
# from the address grammar or split arbitrary addresses on '='. Only these
# explicit, unquoted log-field names receive assignment interpretation.
# Bare 'owner=alice@example.invalid' is inherently ambiguous; this boundary
# treats it as a field. Angle brackets, double-quoted addresses and mailto:
# preserve the complete address. This is a log heuristic, not an RFC parser.
_EMAIL_ASSIGNMENT = re.compile(
    r"(?<![^\s{\[,;])(?i:owner|contact|email|e_mail|email_address|emailaddress)"
    r"[ \t]*=[ \t]*(?P<quote>['\"]?)(?P<value>" + _EMAIL_ADDRESS + r")(?P=quote)"
)

_CHINESE_ID = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}"
    r"(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"
    r"\d{3}[\dXx](?![\dXx])"
)

_CHINESE_PHONE = re.compile(r"(?<!\d)(?:\+?86[-.\s]?)?1[3-9]\d[-.\s]?\d{4}[-.\s]?\d{4}(?!\d)")

_NORTH_AMERICAN_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"
)

_INTERNATIONAL_PHONE = re.compile(r"(?<![\w])\+\d{1,3}(?:[-.\s]?\d){7,13}(?!\d)")

_IPV4_CANDIDATE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")


def _iter_pii_matches(text: str) -> Iterator[_PiiMatch]:
    assignments = [match.span("value") for match in _EMAIL_ASSIGNMENT.finditer(text)]
    for start, end in assignments:
        yield _PiiMatch("EMAIL", start, end, "medium")

    assignment_index = 0
    for match in _EMAIL.finditer(text):
        # Suppress the broader match that includes a field name. A linear
        # merge avoids quadratic scanning when a log has many email fields.
        while (
            assignment_index < len(assignments)
            and assignments[assignment_index][1] <= match.start()
        ):
            assignment_index += 1
        if assignment_index < len(assignments) and assignments[assignment_index][0] < match.end():
            continue
        yield _PiiMatch("EMAIL", *match.span(), "medium")

    for match in _CHINESE_ID.finditer(text):
        yield _PiiMatch("CHINESE_ID", *match.span(), "high")

    for pattern in (_CHINESE_PHONE, _NORTH_AMERICAN_PHONE, _INTERNATIONAL_PHONE):
        for match in pattern.finditer(text):
            yield _PiiMatch("PHONE", *match.span(), "medium")

    for match in _IPV4_CANDIDATE.finditer(text):
        candidate = match.group(0)
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.version == 4:
            yield _PiiMatch("IPV4", *match.span(), "medium")


def detect_pii(text: str, source: str = "<input>") -> list[InternalFinding]:
    """Detect supported PII and resolve overlapping pattern matches."""

    findings = [
        InternalFinding(
            finding_type=match.finding_type,
            severity=match.severity,
            source=source,
            line=line_number(text, match.start),
            detector="regex",
            action=Action.PSEUDONYMIZE,
            sensitivity=Sensitivity.PII,
            span=Span(match.start, match.end),
        )
        for match in _iter_pii_matches(text)
    ]
    return resolve_sensitive_overlaps(findings)
