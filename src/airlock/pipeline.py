"""Deterministic, fail-closed AI Airlock orchestration."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic_ns
from typing import Any

from airlock.audit import append_audit_event, build_audit_event
from airlock.audit.logger import validate_audit_path
from airlock.capsule.builder import Evidence, build_capsule
from airlock.capsule.leak_guard import enforce_no_sensitive_leaks
from airlock.capsule.pseudonymizer import ConsistentPseudonymizer
from airlock.capsule.redactor import transform_text
from airlock.detectors import InternalFinding, Sensitivity, detect_all
from airlock.errors import ConfigurationError, InputIncompleteError
from airlock.ingestion import IngestionResult, InputIncomplete, load_path
from airlock.policy import Policy, PolicyError, load_policy
from airlock.relevance import RankingError, rank_evidence
from airlock.schemas import (
    SCHEMA_VERSION,
    Decision,
    FileStats,
    PublicFinding,
    RiskLevel,
    ScanReport,
    SecuritySummary,
)
from airlock.serialization import stable_json

_PROHIBITED_EXFIL_TASKS = (
    re.compile(
        r"(?is)\b(?:read|collect|extract)\b.{0,100}\b(?:credential|secret|"
        r"private\s+key|api\s+key|environment\s+variable)s?\b.{0,100}"
        r"\b(?:upload|post|send|exfiltrate)\b.{0,100}(?:https?://|webhook)",
    ),
    re.compile(
        r"(?is)\b(?:upload|post|send|exfiltrate)\b.{0,100}\b(?:credential|"
        r"secret|private\s+key|api\s+key|environment\s+variable)s?\b"
        r".{0,100}(?:https?://|webhook)",
    ),
    re.compile(
        r"(?:读取|收集|提取).{0,50}(?:凭证|密钥|私钥|环境变量).{0,50}"
        r"(?:上传|发送|外传).{0,50}(?:https?://|webhook)",
    ),
)


@dataclass(frozen=True, slots=True)
class _PreparedWorkspace:
    ingestion: IngestionResult
    findings: tuple[InternalFinding, ...]
    public_findings: tuple[PublicFinding, ...]
    transformed_documents: dict[str, str]
    sensitive_values: frozenset[str]
    security: SecuritySummary
    decision: Decision
    risk_level: RiskLevel


def _inference_metadata() -> dict[str, Any]:
    return {
        "openvino_available": False,
        "mode": "deterministic_rules",
        "warning": "OpenVINO semantic inference is not enabled in v0.1.",
    }


def _security_summary(findings: tuple[InternalFinding, ...]) -> SecuritySummary:
    counts = Counter(finding.finding_type for finding in findings)
    pii_items = sum(1 for finding in findings if finding.sensitivity is Sensitivity.PII)
    instruction_spans = {
        (finding.source, finding.span.start, finding.span.end)
        for finding in findings
        if finding.sensitivity is Sensitivity.UNTRUSTED_INSTRUCTION
    }
    return SecuritySummary(
        api_keys=counts["API_KEY"],
        bearer_tokens=counts["BEARER_TOKEN"],
        jwt_tokens=counts["JWT"],
        aws_keys=counts["AWS_ACCESS_KEY"],
        private_keys=counts["PRIVATE_KEY"],
        database_credentials=counts["DATABASE_URL"] + counts["CONNECTION_STRING"],
        password_assignments=counts["PASSWORD"],
        emails=counts["EMAIL"],
        phones=counts["PHONE"],
        chinese_ids=counts["CHINESE_ID"],
        ip_addresses=counts["IPV4"],
        pii_items=pii_items,
        prompt_injections=counts["PROMPT_INJECTION"],
        data_exfiltration_attempts=counts["DATA_EXFILTRATION"],
        blocked_instructions=len(instruction_spans),
    )


def _risk_level(findings: tuple[InternalFinding, ...]) -> RiskLevel:
    types = {finding.finding_type for finding in findings}
    if "PRIVATE_KEY" in types:
        return RiskLevel.CRITICAL
    if any(
        finding.sensitivity in {Sensitivity.SECRET, Sensitivity.UNTRUSTED_INSTRUCTION}
        for finding in findings
    ):
        return RiskLevel.HIGH
    if any(finding.sensitivity is Sensitivity.PII for finding in findings):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _decision(findings: tuple[InternalFinding, ...]) -> Decision:
    return Decision.ALLOW_WITH_TRANSFORM if findings else Decision.ALLOW


def _unique_safe_source(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while f"{candidate}#{suffix}" in used:
        suffix += 1
    unique = f"{candidate}#{suffix}"
    used.add(unique)
    return unique


def _public_findings(
    findings: tuple[InternalFinding, ...], source_map: dict[str, str]
) -> tuple[PublicFinding, ...]:
    public = [
        PublicFinding(
            type=finding.finding_type,
            severity=finding.severity,
            source=source_map[finding.source],
            line=finding.line,
            detector=finding.detector,
            action=finding.action.value,
        )
        for finding in findings
    ]
    public.sort(key=lambda item: (item.source, item.line, item.type, item.action))
    return tuple(public)


def _prepare_workspace(
    path: str | Path,
    policy: Policy,
    pseudonymizer: ConsistentPseudonymizer,
) -> _PreparedWorkspace:
    try:
        ingestion = load_path(path, policy.limits.to_ingestion_limits())
    except InputIncomplete:
        raise InputIncompleteError() from None

    all_findings: list[InternalFinding] = []
    findings_by_source: dict[str, list[InternalFinding]] = {}
    for document in ingestion.files:
        detected = detect_all(document.text, document.relative_path)
        findings_by_source[document.relative_path] = detected
        all_findings.extend(detected)

    used_sources: set[str] = set()
    source_map: dict[str, str] = {}
    transformed_documents: dict[str, str] = {}
    sensitive_values: set[str] = set()
    for document in ingestion.files:
        source_findings = detect_all(document.relative_path, "<source>")
        safe_source_result = transform_text(
            document.relative_path,
            source_findings,
            pseudonymizer,
            pii_mode=policy.transform.pii,
            internal_ip_mode=policy.transform.internal_ips,
        )
        sensitive_values.update(safe_source_result.sensitive_values)
        safe_source = _unique_safe_source(safe_source_result.text, used_sources)
        source_map[document.relative_path] = safe_source

        transformed = transform_text(
            document.text,
            findings_by_source[document.relative_path],
            pseudonymizer,
            pii_mode=policy.transform.pii,
            internal_ip_mode=policy.transform.internal_ips,
        )
        sensitive_values.update(transformed.sensitive_values)
        transformed_documents[safe_source] = transformed.text

    materialized = tuple(
        sorted(
            all_findings,
            key=lambda item: (
                item.source,
                item.span.start,
                item.span.end,
                item.finding_type,
            ),
        )
    )
    return _PreparedWorkspace(
        ingestion=ingestion,
        findings=materialized,
        public_findings=_public_findings(materialized, source_map),
        transformed_documents=transformed_documents,
        sensitive_values=frozenset(sensitive_values),
        security=_security_summary(materialized),
        decision=_decision(materialized),
        risk_level=_risk_level(materialized),
    )


def _policy(path: str | Path | None) -> Policy:
    try:
        return load_policy(path)
    except PolicyError:
        raise ConfigurationError() from None


def _audit_target(audit_log: str | Path | None, scan_path: str | Path) -> Path | None:
    if audit_log is None:
        return None
    try:
        return validate_audit_path(Path(audit_log), Path(scan_path))
    except (OSError, RuntimeError, TypeError, ValueError):
        raise InputIncompleteError() from None


def _finalize(
    *,
    result: dict[str, Any],
    sensitive_values: set[str] | frozenset[str],
    audit_path: Path | None,
    operation: str,
    files: FileStats,
    decision: Decision,
    risk_level: RiskLevel,
    security: SecuritySummary,
    started_ns: int,
) -> dict[str, Any]:
    audit_event = build_audit_event(
        operation=operation,
        status="success",
        files_inspected=files.inspected,
        files_skipped=files.skipped,
        decision=decision.value,
        risk_level=risk_level.value,
        security_counts=asdict(security),
        duration_ms=(monotonic_ns() - started_ns) // 1_000_000,
    )
    payloads = [stable_json(result)]
    if audit_path is not None:
        payloads.append(stable_json(audit_event))
    enforce_no_sensitive_leaks(payloads, sensitive_values)
    if audit_path is not None:
        append_audit_event(audit_path, audit_event)
    return result


def scan(
    *,
    path: str | Path,
    policy_path: str | Path | None = None,
    audit_log: str | Path | None = None,
) -> dict[str, Any]:
    started_ns = monotonic_ns()
    policy = _policy(policy_path)
    audit_path = _audit_target(audit_log, path)
    workspace = _prepare_workspace(path, policy, ConsistentPseudonymizer())
    files = FileStats(
        inspected=workspace.ingestion.inspected_files,
        skipped=workspace.ingestion.skipped_files,
        total_bytes=workspace.ingestion.total_bytes,
    )
    report = ScanReport(
        schema_version=SCHEMA_VERSION,
        decision=workspace.decision,
        risk_level=workspace.risk_level,
        files=files,
        findings=workspace.public_findings,
        security=workspace.security,
        inference=_inference_metadata(),
    )
    return _finalize(
        result=report.to_dict(),
        sensitive_values=workspace.sensitive_values,
        audit_path=audit_path,
        operation="scan",
        files=files,
        decision=workspace.decision,
        risk_level=workspace.risk_level,
        security=workspace.security,
        started_ns=started_ns,
    )


def _task_requests_exfiltration(task: str) -> bool:
    return any(pattern.search(task) for pattern in _PROHIBITED_EXFIL_TASKS)


def analyze(
    *,
    task: str,
    path: str | Path,
    policy_path: str | Path | None = None,
    audit_log: str | Path | None = None,
) -> dict[str, Any]:
    started_ns = monotonic_ns()
    policy = _policy(policy_path)
    audit_path = _audit_target(audit_log, path)
    pseudonymizer = ConsistentPseudonymizer()

    task_findings = detect_all(task, "<task>")
    safe_task_result = transform_text(
        task,
        task_findings,
        pseudonymizer,
        pii_mode=policy.transform.pii,
        internal_ip_mode=policy.transform.internal_ips,
    )
    all_sensitive_values = set(safe_task_result.sensitive_values)

    workspace = _prepare_workspace(path, policy, pseudonymizer)
    all_sensitive_values.update(workspace.sensitive_values)
    files = FileStats(
        inspected=workspace.ingestion.inspected_files,
        skipped=workspace.ingestion.skipped_files,
        total_bytes=workspace.ingestion.total_bytes,
    )

    transformed_has_content = any(
        line.strip() and line.strip() != "[UNTRUSTED_INSTRUCTION_ISOLATED]"
        for text in workspace.transformed_documents.values()
        for line in text.splitlines()
    )
    task_blocked = _task_requests_exfiltration(task)
    decision = Decision.BLOCK if task_blocked or not transformed_has_content else workspace.decision
    risk_level = RiskLevel.HIGH if task_blocked else workspace.risk_level

    evidence: list[Evidence] = []
    coverage_warning: str | None = None
    if decision is Decision.BLOCK:
        coverage_warning = "TASK_BLOCKED" if task_blocked else "NO_SAFE_CONTEXT"
    else:
        try:
            ranked = rank_evidence(
                safe_task_result.text,
                workspace.transformed_documents,
                max_tokens=policy.limits.max_capsule_tokens,
                reserved_tokens=min(1000, policy.limits.max_capsule_tokens // 2),
            )
        except RankingError:
            raise InputIncompleteError() from None
        evidence = [
            Evidence(
                text=fact.text,
                source=fact.source,
                start_line=fact.start_line,
                end_line=fact.end_line,
                score=fact.score,
            )
            for fact in ranked.facts
        ]
        if not evidence:
            coverage_warning = ranked.status

    capsule = build_capsule(
        task=safe_task_result.text,
        decision=decision,
        risk_level=risk_level,
        files=files,
        security=workspace.security,
        evidence=evidence,
        original_bytes=workspace.ingestion.total_bytes,
        max_capsule_tokens=policy.limits.max_capsule_tokens,
        coverage_warning=coverage_warning,
    )
    return _finalize(
        result=capsule.to_dict(),
        sensitive_values=all_sensitive_values,
        audit_path=audit_path,
        operation="analyze",
        files=files,
        decision=decision,
        risk_level=risk_level,
        security=workspace.security,
        started_ns=started_ns,
    )


def health() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "version": "0.1.0",
        "commands": ["health", "scan", "analyze"],
        "inference": _inference_metadata(),
    }
