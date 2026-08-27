"""Deterministic overlap handling for detector findings."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Final

from .models import InternalFinding, Sensitivity

# Lower is preferred when sensitivity and matched length are identical.  The
# ordering favours the more structurally specific detector.
TYPE_PRIORITY: Final[dict[str, int]] = {
    "PRIVATE_KEY": 0,
    "DATABASE_URL": 1,
    "CONNECTION_STRING": 2,
    "BEARER_TOKEN": 3,
    "JWT": 4,
    "AWS_ACCESS_KEY": 5,
    "PASSWORD": 6,
    "API_KEY": 7,
    "CHINESE_ID": 20,
    "EMAIL": 21,
    "PHONE": 22,
    "IPV4": 23,
}


def _preference(finding: InternalFinding) -> tuple[int, int, int, int, str]:
    sensitivity_rank = 0 if finding.sensitivity is Sensitivity.SECRET else 1
    return (
        sensitivity_rank,
        -finding.span.length,
        TYPE_PRIORITY.get(finding.finding_type, 10_000),
        finding.span.start,
        finding.finding_type,
    )


def resolve_sensitive_overlaps(
    findings: Iterable[InternalFinding],
) -> list[InternalFinding]:
    """Resolve sensitive intervals: Secret, then length, then fixed type order.

    Sources are independent coordinate spaces and are therefore resolved in
    separate groups.  Non-sensitive instruction findings are not returned by
    this function.
    """

    grouped: dict[str, list[InternalFinding]] = defaultdict(list)
    for finding in findings:
        if finding.sensitivity in {Sensitivity.SECRET, Sensitivity.PII}:
            grouped[finding.source].append(finding)

    resolved: list[InternalFinding] = []
    for source in sorted(grouped):
        accepted: list[InternalFinding] = []
        seen: set[tuple[str, int, int]] = set()
        for candidate in sorted(grouped[source], key=_preference):
            identity = (
                candidate.finding_type,
                candidate.span.start,
                candidate.span.end,
            )
            if identity in seen:
                continue
            seen.add(identity)
            if any(candidate.span.overlaps(current.span) for current in accepted):
                continue
            accepted.append(candidate)
        resolved.extend(
            sorted(
                accepted,
                key=lambda item: (
                    item.span.start,
                    item.span.end,
                    TYPE_PRIORITY.get(item.finding_type, 10_000),
                ),
            )
        )
    return resolved


def resolve_overlaps(findings: Iterable[InternalFinding]) -> list[InternalFinding]:
    """Resolve sensitive spans while retaining instruction classifications.

    Prompt-injection and exfiltration findings form a separate semantic layer:
    the same untrusted block can correctly have both classifications.  Their
    intervals are merged only when text is transformed, not when counts are
    aggregated.
    """

    materialized = list(findings)
    sensitive = resolve_sensitive_overlaps(materialized)
    instructions: list[InternalFinding] = []
    seen: set[tuple[str, str | None, str, int, int]] = set()
    for finding in materialized:
        if finding.sensitivity is not Sensitivity.UNTRUSTED_INSTRUCTION:
            continue
        identity = (
            finding.finding_type,
            finding.category,
            finding.source,
            finding.span.start,
            finding.span.end,
        )
        if identity not in seen:
            seen.add(identity)
            instructions.append(finding)

    return sorted(
        [*sensitive, *instructions],
        key=lambda item: (
            item.source,
            item.span.start,
            item.span.end,
            item.finding_type,
            item.category or "",
        ),
    )
