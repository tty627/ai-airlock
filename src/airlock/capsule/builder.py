"""Deterministic Safe Context Capsule builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from airlock.errors import PolicyLimitError
from airlock.schemas import (
    Decision,
    FileStats,
    RiskLevel,
    SafeContext,
    SafeContextCapsule,
    SafeFact,
    SecuritySummary,
)
from airlock.serialization import estimate_tokens

TOKEN_ESTIMATOR = "utf8_bytes_div_4_ceil_v1"


@dataclass(frozen=True, slots=True)
class Evidence:
    text: str
    source: str
    start_line: int
    end_line: int
    score: int


def _with_metrics(
    *,
    task: str,
    decision: Decision,
    risk_level: RiskLevel,
    files: FileStats,
    security: SecuritySummary,
    facts: tuple[SafeFact, ...],
    coverage_warning: str | None,
    original_tokens: int,
) -> SafeContextCapsule:
    capsule_tokens = 0
    capsule: SafeContextCapsule | None = None
    for _ in range(12):
        reduction = round(1 - (capsule_tokens / original_tokens), 6) if original_tokens else 0.0
        capsule = SafeContextCapsule(
            schema_version="0.1",
            task=task,
            decision=decision,
            risk_level=risk_level,
            files=files,
            safe_context=SafeContext(
                facts=facts,
                coverage_warning=coverage_warning,
            ),
            security=security,
            privacy={"raw_sensitive_spans_forwarded": 0},
            efficiency={
                "original_tokens_estimated": original_tokens,
                "capsule_tokens_estimated": capsule_tokens,
                "reduction_ratio": reduction,
                "estimator": TOKEN_ESTIMATOR,
            },
            inference={
                "openvino_available": False,
                "mode": "deterministic_rules",
                "warning": "OpenVINO semantic inference is not enabled in v0.1.",
            },
        )
        next_estimate = estimate_tokens(capsule.to_dict())
        if next_estimate == capsule_tokens:
            return capsule
        capsule_tokens = next_estimate
    if capsule is None:  # pragma: no cover - defensive only
        raise PolicyLimitError()
    return capsule


def build_capsule(
    *,
    task: str,
    decision: Decision,
    risk_level: RiskLevel,
    files: FileStats,
    security: SecuritySummary,
    evidence: list[Evidence],
    original_bytes: int,
    max_capsule_tokens: int,
    coverage_warning: str | None = None,
) -> SafeContextCapsule:
    """Build the largest stable evidence set that fits the full JSON budget."""

    original_tokens = (original_bytes + 3) // 4
    accepted: list[SafeFact] = []
    warning = coverage_warning if not evidence else None

    base = _with_metrics(
        task=task,
        decision=decision,
        risk_level=risk_level,
        files=files,
        security=security,
        facts=(),
        coverage_warning=warning,
        original_tokens=original_tokens,
    )
    if estimate_tokens(base.to_dict()) > max_capsule_tokens:
        raise PolicyLimitError()

    for item in evidence:
        candidate = SafeFact(
            id=f"fact_{len(accepted) + 1:03d}",
            text=item.text,
            source=item.source,
            local_ref=(
                f"L{item.start_line}"
                if item.start_line == item.end_line
                else f"L{item.start_line}-L{item.end_line}"
            ),
            selection_score=item.score,
        )
        trial = _with_metrics(
            task=task,
            decision=decision,
            risk_level=risk_level,
            files=files,
            security=security,
            facts=tuple([*accepted, candidate]),
            coverage_warning=None,
            original_tokens=original_tokens,
        )
        if estimate_tokens(trial.to_dict()) <= max_capsule_tokens:
            accepted.append(candidate)

    return _with_metrics(
        task=task,
        decision=decision,
        risk_level=risk_level,
        files=files,
        security=security,
        facts=tuple(accepted),
        coverage_warning=warning if not accepted else None,
        original_tokens=original_tokens,
    )


def capsule_json_ready(capsule: SafeContextCapsule) -> dict[str, Any]:
    """Named boundary for callers that emit a public Capsule."""

    return capsule.to_dict()
