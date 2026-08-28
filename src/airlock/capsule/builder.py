"""Deterministic Safe Context Capsule builder."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from airlock.capsule.leak_guard import inspect_public_payload
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
_DETERMINISTIC_INFERENCE = {
    "openvino_available": False,
    "mode": "deterministic_rules",
    "warning": "OpenVINO semantic inference is not enabled in v0.1.",
}


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
    selection_method: str,
    inference: dict[str, Any],
    sensitive_values: tuple[str, ...],
) -> SafeContextCapsule:
    capsule_tokens = 0
    capsule: SafeContextCapsule | None = None
    for _ in range(12):
        reduction = round(1 - (capsule_tokens / original_tokens), 6) if original_tokens else 0.0
        safe_context = SafeContext(
            facts=facts,
            coverage_warning=coverage_warning,
            selection_method=selection_method,
        )
        inspection = inspect_public_payload(
            {"task": task, "safe_context": safe_context.to_dict()},
            sensitive_values,
        )
        capsule = SafeContextCapsule(
            schema_version="0.1",
            task=task,
            decision=decision,
            risk_level=risk_level,
            files=files,
            safe_context=safe_context,
            security=security,
            privacy={"raw_sensitive_spans_forwarded": inspection.raw_sensitive_spans_forwarded},
            efficiency={
                "original_tokens_estimated": original_tokens,
                "capsule_tokens_estimated": capsule_tokens,
                "reduction_ratio": reduction,
                "estimator": TOKEN_ESTIMATOR,
            },
            inference=dict(inference),
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
    sensitive_values: Iterable[str],
    coverage_warning: str | None = None,
    selection_method: str = "deterministic_lexical_v1",
    inference: dict[str, Any] | None = None,
) -> SafeContextCapsule:
    """Build the largest stable evidence set that fits the full JSON budget."""

    original_tokens = (original_bytes + 3) // 4
    accepted: list[SafeFact] = []
    warning = coverage_warning if not evidence else None
    inference_metadata = dict(_DETERMINISTIC_INFERENCE if inference is None else inference)
    protected_values = tuple(sensitive_values)

    base = _with_metrics(
        task=task,
        decision=decision,
        risk_level=risk_level,
        files=files,
        security=security,
        facts=(),
        coverage_warning=warning,
        original_tokens=original_tokens,
        selection_method=selection_method,
        inference=inference_metadata,
        sensitive_values=protected_values,
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
            selection_method=selection_method,
            inference=inference_metadata,
            sensitive_values=protected_values,
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
        selection_method=selection_method,
        inference=inference_metadata,
        sensitive_values=protected_values,
    )


def capsule_json_ready(capsule: SafeContextCapsule) -> dict[str, Any]:
    """Named boundary for callers that emit a public Capsule."""

    return capsule.to_dict()
