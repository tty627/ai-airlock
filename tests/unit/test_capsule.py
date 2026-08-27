from __future__ import annotations

from airlock.capsule.builder import Evidence, build_capsule
from airlock.schemas import Decision, FileStats, RiskLevel, SecuritySummary
from airlock.serialization import estimate_tokens, stable_json


def _build():
    return build_capsule(
        task="diagnose the failure",
        decision=Decision.ALLOW_WITH_TRANSFORM,
        risk_level=RiskLevel.HIGH,
        files=FileStats(inspected=2, skipped=0, total_bytes=2000),
        security=SecuritySummary(api_keys=1),
        evidence=[
            Evidence(
                text="ERROR connection pool exhausted",
                source="service.log",
                start_line=10,
                end_line=10,
                score=9,
            )
        ],
        original_bytes=2000,
        max_capsule_tokens=1000,
    )


def test_capsule_metrics_are_measured_and_stable() -> None:
    first = _build()
    second = _build()

    assert stable_json(first.to_dict()) == stable_json(second.to_dict())
    assert first.efficiency["capsule_tokens_estimated"] == estimate_tokens(first.to_dict())
    assert first.safe_context.facts[0].local_ref == "L10"
    assert first.privacy["raw_sensitive_spans_forwarded"] == 0


def test_capsule_reports_no_relevant_context_without_fallback_disclosure() -> None:
    capsule = build_capsule(
        task="unmatched",
        decision=Decision.ALLOW,
        risk_level=RiskLevel.LOW,
        files=FileStats(inspected=1, skipped=0, total_bytes=100),
        security=SecuritySummary(),
        evidence=[],
        original_bytes=100,
        max_capsule_tokens=1000,
        coverage_warning="NO_RELEVANT_CONTEXT",
    )

    assert capsule.safe_context.facts == ()
    assert capsule.safe_context.coverage_warning == "NO_RELEVANT_CONTEXT"
