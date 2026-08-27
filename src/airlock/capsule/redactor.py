"""One-pass isolation, Secret redaction and PII pseudonymization."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from airlock.detectors import (
    InternalFinding,
    Sensitivity,
    Span,
    resolve_sensitive_overlaps,
)

from .pseudonymizer import ConsistentPseudonymizer


class SensitiveValues:
    """Opaque, in-memory values used by the final leak gate.

    Iteration is available to the leak checker, but repr/str never disclose the
    stored values and there is deliberately no serialisation method.
    """

    __slots__ = ("_values",)

    def __init__(self, values: Iterable[str] = ()) -> None:
        self._values = frozenset(value for value in values if value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __contains__(self, value: object) -> bool:
        return value in self._values

    def __len__(self) -> int:
        return len(self._values)

    def __bool__(self) -> bool:
        return bool(self._values)

    def appears_in(self, payload: str) -> bool:
        """Return whether any protected original occurs in a candidate output."""

        return any(value in payload for value in self._values)

    def __repr__(self) -> str:
        return f"SensitiveValues(count={len(self)})"

    __str__ = __repr__


@dataclass(frozen=True, slots=True, repr=False)
class TransformationResult:
    """A safe transformed document plus opaque leak-gate material."""

    text: str
    sensitive_values: SensitiveValues
    replacement_count: int
    isolated_instruction_count: int

    def __repr__(self) -> str:
        return (
            "TransformationResult("
            f"text_length={len(self.text)}, "
            f"sensitive_values={self.sensitive_values!r}, "
            f"replacement_count={self.replacement_count}, "
            f"isolated_instruction_count={self.isolated_instruction_count})"
        )


def _merge_spans(spans: Iterable[Span]) -> list[Span]:
    ordered = sorted(spans, key=lambda span: (span.start, span.end))
    if not ordered:
        return []

    merged: list[Span] = [ordered[0]]
    for span in ordered[1:]:
        current = merged[-1]
        if span.start <= current.end:
            merged[-1] = Span(current.start, max(current.end, span.end))
        else:
            merged.append(span)
    return merged


def _expand_quarantine(quarantined: list[Span], sensitive: list[InternalFinding]) -> list[Span]:
    """Ensure a partially overlapping sensitive span cannot be left behind."""

    current = quarantined
    while current:
        expanded: list[Span] = []
        for interval in current:
            start, end = interval.start, interval.end
            for finding in sensitive:
                if Span(start, end).overlaps(finding.span):
                    start = min(start, finding.span.start)
                    end = max(end, finding.span.end)
            expanded.append(Span(start, end))
        merged = _merge_spans(expanded)
        if merged == current:
            return merged
        current = merged
    return current


def _inside_any(span: Span, intervals: list[Span]) -> bool:
    return any(interval.contains(span) for interval in intervals)


def _secret_label(finding_type: str) -> str:
    return f"[{finding_type}_REDACTED]"


def transform_text(
    text: str,
    findings: Iterable[InternalFinding],
    pseudonymizer: ConsistentPseudonymizer | None = None,
    *,
    pii_mode: str = "pseudonymize",
    internal_ip_mode: str = "pseudonymize",
) -> TransformationResult:
    """Apply all deterministic transforms against one original coordinate set.

    Instruction intervals are quarantined first.  Secret/PII overlaps are then
    resolved using the detector policy, and sensitive spans outside quarantine
    are replaced in one pass so offsets never drift.
    """

    if pii_mode not in {"pseudonymize", "redact"}:
        raise ValueError("invalid pii mode")
    if internal_ip_mode not in {"pseudonymize", "redact"}:
        raise ValueError("invalid internal IP mode")

    materialized = list(findings)
    sensitive = resolve_sensitive_overlaps(materialized)
    for finding in materialized:
        if finding.span.end > len(text):
            raise ValueError("finding outside document")

    quarantined = _merge_spans(
        finding.span
        for finding in materialized
        if finding.sensitivity is Sensitivity.UNTRUSTED_INSTRUCTION
    )
    quarantined = _expand_quarantine(quarantined, sensitive)

    originals = SensitiveValues(
        [
            *(text[finding.span.start : finding.span.end] for finding in sensitive),
            *(text[interval.start : interval.end] for interval in quarantined),
        ]
    )
    engine = pseudonymizer if pseudonymizer is not None else ConsistentPseudonymizer()

    replacements: list[tuple[int, int, str, bool]] = [
        (
            interval.start,
            interval.end,
            "[UNTRUSTED_INSTRUCTION_ISOLATED]",
            True,
        )
        for interval in quarantined
    ]
    for finding in sensitive:
        if _inside_any(finding.span, quarantined):
            continue
        original = text[finding.span.start : finding.span.end]
        if finding.sensitivity is Sensitivity.SECRET:
            replacement = _secret_label(finding.finding_type)
        else:
            active_mode = internal_ip_mode if finding.finding_type == "IPV4" else pii_mode
            replacement = (
                engine.pseudonym_for(finding.finding_type, original)
                if active_mode == "pseudonymize"
                else f"[{finding.finding_type}_REDACTED]"
            )
        replacements.append((finding.span.start, finding.span.end, replacement, False))

    replacements.sort(key=lambda item: (item[0], item[1]))
    pieces: list[str] = []
    cursor = 0
    for start, end, replacement, _ in replacements:
        if start < cursor:
            raise ValueError("unresolved transformation overlap")
        pieces.extend((text[cursor:start], replacement))
        cursor = end
    pieces.append(text[cursor:])

    return TransformationResult(
        text="".join(pieces),
        sensitive_values=originals,
        replacement_count=len(replacements),
        isolated_instruction_count=len(quarantined),
    )


def redact_secrets(text: str, findings: Iterable[InternalFinding]) -> TransformationResult:
    """Redact only Secret findings using fixed type labels."""

    return transform_text(
        text,
        (finding for finding in findings if finding.sensitivity is Sensitivity.SECRET),
    )


def isolate_instructions(text: str, findings: Iterable[InternalFinding]) -> TransformationResult:
    """Isolate only prompt-injection/data-exfiltration spans."""

    return transform_text(
        text,
        (
            finding
            for finding in findings
            if finding.sensitivity is Sensitivity.UNTRUSTED_INSTRUCTION
        ),
    )


__all__ = [
    "SensitiveValues",
    "TransformationResult",
    "isolate_instructions",
    "redact_secrets",
    "transform_text",
]
