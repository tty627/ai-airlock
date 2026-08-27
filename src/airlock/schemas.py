"""Stable public schemas for deterministic AI Airlock output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = "0.1"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    ALLOW_WITH_TRANSFORM = "ALLOW_WITH_TRANSFORM"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    BLOCK = "BLOCK"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class PublicFinding:
    type: str
    severity: str
    source: str
    line: int
    detector: str
    action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FileStats:
    inspected: int
    skipped: int
    total_bytes: int


@dataclass(frozen=True, slots=True)
class SecuritySummary:
    api_keys: int = 0
    bearer_tokens: int = 0
    jwt_tokens: int = 0
    aws_keys: int = 0
    private_keys: int = 0
    database_credentials: int = 0
    password_assignments: int = 0
    emails: int = 0
    phones: int = 0
    chinese_ids: int = 0
    ip_addresses: int = 0
    pii_items: int = 0
    prompt_injections: int = 0
    data_exfiltration_attempts: int = 0
    blocked_instructions: int = 0


@dataclass(frozen=True, slots=True)
class ScanReport:
    schema_version: str
    decision: Decision
    risk_level: RiskLevel
    files: FileStats
    findings: tuple[PublicFinding, ...]
    security: SecuritySummary
    inference: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "files": asdict(self.files),
            "findings": [finding.to_dict() for finding in self.findings],
            "security": asdict(self.security),
            "inference": self.inference,
        }


@dataclass(frozen=True, slots=True)
class SafeFact:
    id: str
    text: str
    source: str
    local_ref: str
    selection_score: int


@dataclass(frozen=True, slots=True)
class SafeContext:
    summary: None = None
    facts: tuple[SafeFact, ...] = field(default_factory=tuple)
    coverage_warning: str | None = None
    selection_method: str = "deterministic_lexical_v1"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "summary": None,
            "facts": [asdict(fact) for fact in self.facts],
            "selection_method": self.selection_method,
        }
        if self.coverage_warning is not None:
            result["coverage_warning"] = self.coverage_warning
        return result


@dataclass(frozen=True, slots=True)
class SafeContextCapsule:
    schema_version: str
    task: str
    decision: Decision
    risk_level: RiskLevel
    files: FileStats
    safe_context: SafeContext
    security: SecuritySummary
    privacy: dict[str, int]
    efficiency: dict[str, Any]
    inference: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task": self.task,
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "files": asdict(self.files),
            "safe_context": self.safe_context.to_dict(),
            "security": asdict(self.security),
            "privacy": self.privacy,
            "efficiency": self.efficiency,
            "inference": self.inference,
        }
