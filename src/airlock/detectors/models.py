"""Internal, value-free finding types used by deterministic detectors.

The detector boundary deliberately stores offsets instead of matched values.  A
caller that needs to transform a document can recover a value from the original
in-memory text, while serialising or logging a finding cannot disclose it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final


class Sensitivity(StrEnum):
    """The processing layer to which a finding belongs."""

    SECRET = "secret"
    PII = "pii"
    UNTRUSTED_INSTRUCTION = "untrusted_instruction"


class Action(StrEnum):
    """Deterministic action attached to an internal finding."""

    REDACT = "REDACT"
    PSEUDONYMIZE = "PSEUDONYMIZE"
    ISOLATE = "ISOLATE"


@dataclass(frozen=True, slots=True)
class Span:
    """A half-open character interval into one in-memory document."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("invalid finding span")

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: Span) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: Span) -> bool:
        return self.start <= other.start and self.end >= other.end


_WINDOWS_ABSOLUTE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:/")


def safe_source(source: str) -> str:
    """Return a stable relative source without retaining an absolute path."""

    normalized = source.replace("\\", "/")
    if normalized.startswith("/") or _WINDOWS_ABSOLUTE.match(normalized):
        return PurePosixPath(normalized).name or "<input>"
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if ".." in parts:
        return parts[-1] if parts and parts[-1] != ".." else "<input>"
    return "/".join(parts) or "<input>"


@dataclass(frozen=True, slots=True, repr=False)
class InternalFinding:
    """A detector result that is safe to repr and safe to make public.

    ``category`` is internal routing metadata.  It is intentionally excluded
    from ``to_public_dict`` so the public Finding shape stays allow-list based.
    The category is still available to aggregate injection and exfiltration
    counts without inspecting the source text.
    """

    finding_type: str
    severity: str
    source: str
    line: int
    detector: str
    action: Action
    sensitivity: Sensitivity
    span: Span
    category: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", safe_source(self.source))
        if self.line < 1:
            raise ValueError("invalid finding line")

    @property
    def type(self) -> str:
        """Compatibility alias for the public ``type`` field."""

        return self.finding_type

    def to_public_dict(self) -> dict[str, str | int]:
        """Return exactly the fields permitted in a public Finding."""

        return {
            "type": self.finding_type,
            "severity": self.severity,
            "source": self.source,
            "line": self.line,
            "detector": self.detector,
            "action": self.action.value,
        }

    def __repr__(self) -> str:
        return (
            "InternalFinding("
            f"type={self.finding_type!r}, severity={self.severity!r}, "
            f"source='<source>', line={self.line}, "
            f"detector={self.detector!r}, action={self.action.value!r}, "
            f"sensitivity={self.sensitivity.value!r}, span={self.span!r})"
        )


def line_number(text: str, offset: int) -> int:
    """Translate a zero-based character offset into a one-based line number."""

    return text.count("\n", 0, offset) + 1
