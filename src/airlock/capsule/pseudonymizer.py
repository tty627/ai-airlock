"""Run-scoped, consistent PII pseudonymization."""

from __future__ import annotations

import ipaddress
import re
from collections import defaultdict
from collections.abc import Iterable

from airlock.detectors import (
    InternalFinding,
    Sensitivity,
    resolve_sensitive_overlaps,
)

_PII_TYPES = frozenset({"EMAIL", "PHONE", "CHINESE_ID", "IPV4"})
_NON_DIGIT = re.compile(r"\D+")


def _identity_value(kind: str, value: str) -> str:
    if kind == "EMAIL":
        return value.casefold()
    if kind == "PHONE":
        digits = _NON_DIGIT.sub("", value)
        if not digits:
            raise ValueError("invalid pseudonym value")
        return ("+" if value.lstrip().startswith("+") else "") + digits
    if kind == "CHINESE_ID":
        return value.upper()
    if kind == "IPV4":
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            raise ValueError("invalid pseudonym value") from None
    raise ValueError("unsupported pseudonym type")


class ConsistentPseudonymizer:
    """Assign stable type-local sequence labels for one pipeline run.

    Mappings intentionally have no persistence or export interface.  Reuse one
    instance across all files in a run and discard it after the final leak gate.
    """

    __slots__ = ("_counters", "_mappings")

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._mappings: dict[tuple[str, str], str] = {}

    def pseudonym_for(self, finding_type: str, value: str) -> str:
        kind = finding_type.upper()
        if kind not in _PII_TYPES:
            raise ValueError("unsupported pseudonym type")
        if not value:
            raise ValueError("empty sensitive value")

        identity = (kind, _identity_value(kind, value))
        existing = self._mappings.get(identity)
        if existing is not None:
            return existing

        self._counters[kind] += 1
        pseudonym = f"[{kind}_{self._counters[kind]:03d}]"
        self._mappings[identity] = pseudonym
        return pseudonym

    def __len__(self) -> int:
        return len(self._mappings)

    def __repr__(self) -> str:
        return f"ConsistentPseudonymizer(assignments={len(self)})"


def pseudonymize_text(
    text: str,
    findings: Iterable[InternalFinding],
    pseudonymizer: ConsistentPseudonymizer | None = None,
) -> str:
    """Replace PII findings while preserving first-occurrence numbering."""

    engine = pseudonymizer if pseudonymizer is not None else ConsistentPseudonymizer()
    pii_findings = resolve_sensitive_overlaps(
        finding for finding in findings if finding.sensitivity is Sensitivity.PII
    )
    replacements: list[tuple[int, int, str]] = []
    for finding in sorted(pii_findings, key=lambda item: item.span.start):
        if finding.span.end > len(text):
            raise ValueError("finding outside document")
        value = text[finding.span.start : finding.span.end]
        replacements.append(
            (
                finding.span.start,
                finding.span.end,
                engine.pseudonym_for(finding.finding_type, value),
            )
        )

    pieces: list[str] = []
    cursor = 0
    for start, end, replacement in replacements:
        pieces.extend((text[cursor:start], replacement))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


__all__ = ["ConsistentPseudonymizer", "pseudonymize_text"]
