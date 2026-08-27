"""High-recall prompt-injection and data-exfiltration heuristics."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .models import Action, InternalFinding, Sensitivity, Span, line_number

_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
_NONEMPTY_LINE = re.compile(r"[^\r\n]+")

_INJECTION_PATTERNS = (
    re.compile(r"\bignore\b.{0,60}\bprevious\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+override\b", re.IGNORECASE),
    re.compile(
        r"\boverride\b.{0,40}\b(?:policy|safety|instructions?|guardrails?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bdisable\b.{0,40}\b(?:safety|security|guardrails?)\b", re.IGNORECASE),
    re.compile(r"\bexecute\b.{0,30}\bcommands?\b", re.IGNORECASE),
    re.compile(r"\bhidden\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(?:the\s+)?system\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+obey\b", re.IGNORECASE),
)

_EXFILTRATION_PATTERNS = (
    re.compile(r"\breveal\b.{0,50}\b(?:secrets?|credentials?|tokens?|keys?)\b", re.IGNORECASE),
    re.compile(
        r"\bread\b.{0,50}\b(?:environment\s+variables?|env(?:ironment)?\s+vars?|"
        r"credentials?|private\s+keys?|secrets?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:^|[\s'\"])(?:~/|/[^\s]*)?\.ssh(?:/|\b)", re.IGNORECASE),
    re.compile(r"\b(?:curl|wget)\b", re.IGNORECASE),
    re.compile(r"\b(?:post|upload|exfiltrate|exfiltration)\b", re.IGNORECASE),
    re.compile(
        r"\bsend\b.{0,80}\b(?:secrets?|credentials?|tokens?|keys?|environment|"
        r"external\s+(?:server|endpoint)|webhook)\b",
        re.IGNORECASE,
    ),
)


def _categories(chunk: str) -> tuple[str, ...]:
    categories: list[str] = []
    if any(pattern.search(chunk) for pattern in _INJECTION_PATTERNS):
        categories.append("injection")
    if any(pattern.search(chunk) for pattern in _EXFILTRATION_PATTERNS):
        categories.append("data_exfiltration")
    return tuple(categories)


def _finding(*, category: str, source: str, text: str, start: int, end: int) -> InternalFinding:
    exfiltration = category == "data_exfiltration"
    return InternalFinding(
        finding_type="DATA_EXFILTRATION" if exfiltration else "PROMPT_INJECTION",
        severity="critical" if exfiltration else "high",
        source=source,
        line=line_number(text, start),
        detector="heuristic",
        action=Action.ISOLATE,
        sensitivity=Sensitivity.UNTRUSTED_INSTRUCTION,
        span=Span(start, end),
        category=category,
    )


def _overlaps_any(span: Span, intervals: list[Span]) -> bool:
    return any(span.overlaps(interval) for interval in intervals)


def _iter_injection_findings(text: str, source: str) -> Iterator[InternalFinding]:
    risky_comments: list[Span] = []
    for match in _HTML_COMMENT.finditer(text):
        categories = _categories(match.group(0))
        if not categories:
            continue
        interval = Span(*match.span())
        risky_comments.append(interval)
        for category in categories:
            yield _finding(
                category=category,
                source=source,
                text=text,
                start=interval.start,
                end=interval.end,
            )

    for match in _NONEMPTY_LINE.finditer(text):
        interval = Span(*match.span())
        if _overlaps_any(interval, risky_comments):
            continue
        for category in _categories(match.group(0)):
            yield _finding(
                category=category,
                source=source,
                text=text,
                start=interval.start,
                end=interval.end,
            )


def detect_injections(text: str, source: str = "<input>") -> list[InternalFinding]:
    """Classify risky comments/lines without retaining their contents."""

    return list(_iter_injection_findings(text, source))
