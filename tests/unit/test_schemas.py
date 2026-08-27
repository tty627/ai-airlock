from __future__ import annotations

from airlock.schemas import Decision, FileStats, RiskLevel, ScanReport, SecuritySummary
from airlock.serialization import stable_json


def test_scan_report_serializes_to_stable_public_shape() -> None:
    report = ScanReport(
        schema_version="0.1",
        decision=Decision.ALLOW,
        risk_level=RiskLevel.LOW,
        files=FileStats(inspected=1, skipped=0, total_bytes=3),
        findings=(),
        security=SecuritySummary(),
        inference={"mode": "deterministic_rules", "openvino_available": False},
    )

    first = stable_json(report.to_dict())
    second = stable_json(report.to_dict())

    assert first == second
    assert '"decision":"ALLOW"' in first
    assert '"schema_version":"0.1"' in first
