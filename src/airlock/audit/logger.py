"""Metadata-only audit logging."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from airlock.errors import InputIncompleteError
from airlock.serialization import stable_json


def validate_audit_path(audit_path: Path, scan_path: Path) -> Path:
    resolved_audit = audit_path.expanduser().resolve(strict=False)
    resolved_scan = scan_path.expanduser().resolve(strict=False)
    scan_root = resolved_scan if resolved_scan.is_dir() else resolved_scan.parent
    try:
        resolved_audit.relative_to(scan_root)
    except ValueError:
        return resolved_audit
    raise InputIncompleteError()


def build_audit_event(
    *,
    operation: str,
    status: str,
    files_inspected: int,
    files_skipped: int,
    decision: str,
    risk_level: str,
    security_counts: dict[str, int],
    duration_ms: int,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "operation": operation,
        "status": status,
        "files_inspected": files_inspected,
        "files_skipped": files_skipped,
        "decision": decision,
        "risk_level": risk_level,
        "security": security_counts,
        "inference_mode": "deterministic_rules",
        "duration_ms": max(0, duration_ms),
    }


def append_audit_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(stable_json(event))
        handle.write("\n")
