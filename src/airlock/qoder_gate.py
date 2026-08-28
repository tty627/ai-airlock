"""Strict, stdlib-only gate for JSON released by the Qoder wrapper.

The wrapper must not forward a child process response until this module has
validated the complete v0.1 shape and rebuilt an allowlisted JSON document.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Sequence
from typing import Any, NoReturn

from airlock.capsule.leak_guard import inspect_public_payload

SCHEMA_VERSION = "0.1"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

_DECISIONS = {"ALLOW", "ALLOW_WITH_TRANSFORM", "REQUIRE_CONFIRMATION", "BLOCK"}
_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
_COVERAGE_WARNINGS = {
    "NO_RELEVANT_CONTEXT",
    "NO_SAFE_CONTEXT",
    "TASK_BLOCKED",
    "TOKEN_BUDGET_EXHAUSTED",
}
_SECURITY_FIELDS = {
    "api_keys",
    "aws_keys",
    "bearer_tokens",
    "blocked_instructions",
    "chinese_ids",
    "data_exfiltration_attempts",
    "database_credentials",
    "emails",
    "ip_addresses",
    "jwt_tokens",
    "password_assignments",
    "phones",
    "pii_items",
    "private_keys",
    "prompt_injections",
}
_ERRORS_BY_CODE = {
    "AIRLOCK_ERROR": "AI Airlock could not complete the request safely.",
    "AIRLOCK_RUNTIME_UNAVAILABLE": (
        "The AI Airlock runtime or a required dependency is unavailable."
    ),
    "AUDIT_LOG_WRITE_FAILED": "AI Airlock could not write the requested audit log.",
    "INFERENCE_UNAVAILABLE": "The requested local inference backend is unavailable.",
    "INPUT_INCOMPLETE": "The input could not be scanned completely; no result was released.",
    "INPUT_PATH_NOT_FOUND": "The requested input path does not exist.",
    "INPUT_PERMISSION_DENIED": ("AI Airlock does not have permission to read the complete input."),
    "INTERNAL_ERROR": "AI Airlock could not complete the request safely.",
    "INVALID_ARGUMENTS": "The command arguments are invalid.",
    "INVALID_CONFIGURATION": "The policy configuration is invalid.",
    "LEAKAGE_GUARD_FAILED": "The output safety check failed; no result was released.",
    "NO_SAFE_CONTEXT": "No safe context could be released for this task.",
    "POLICY_LIMIT_EXCEEDED": "A policy limit prevented safe result generation.",
    "TASK_BLOCKED": "The task violates the active disclosure policy.",
}

_LOCAL_REF = re.compile(r"^L([1-9]\d*)(?:-L([1-9]\d*))?$")
_FACT_ID = re.compile(r"^fact_([0-9]{3})$")


class GateError(Exception):
    """Internal validation failure with no attacker-controlled public text."""


def _reject_constant(_value: str) -> NoReturn:
    raise GateError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError
        result[key] = value
    return result


def _load(serialized: str) -> dict[str, Any]:
    try:
        value = json.loads(
            serialized,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (GateError, json.JSONDecodeError, RecursionError, UnicodeError):
        raise GateError from None
    if type(value) is not dict:
        raise GateError
    return value


def _keys(
    value: Any,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise GateError
    allowed = required | (optional or set())
    if not required <= set(value) or not set(value) <= allowed:
        raise GateError
    return value


def _string(value: Any, *, expected: str | None = None) -> str:
    if type(value) is not str or not value.strip():
        raise GateError
    if expected is not None and value != expected:
        raise GateError
    return value


def _boolean(value: Any, *, expected: bool | None = None) -> bool:
    if type(value) is not bool:
        raise GateError
    if expected is not None and value is not expected:
        raise GateError
    return value


def _integer(
    value: Any,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if type(value) is not int or value < minimum:
        raise GateError
    if maximum is not None and value > maximum:
        raise GateError
    return value


def _number(
    value: Any,
    *,
    maximum: float | None = None,
) -> int | float:
    if type(value) not in {int, float} or not math.isfinite(float(value)):
        raise GateError
    if maximum is not None and float(value) > maximum:
        raise GateError
    return value


def _relative_source(value: Any) -> str:
    source = _string(value)
    components = source.split("/")
    if (
        source.startswith("/")
        or "\\" in source
        or ":" in source
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in source)
        or any(component in {"", ".", ".."} for component in components)
    ):
        raise GateError
    return source


def _files(value: Any) -> None:
    payload = _keys(value, {"inspected", "skipped", "total_bytes"})
    for field in payload.values():
        _integer(field)


def _security(value: Any) -> None:
    payload = _keys(value, _SECURITY_FIELDS)
    for field in payload.values():
        _integer(field)


def _deterministic_inference(value: Any) -> None:
    payload = _keys(value, {"mode", "openvino_available", "warning"})
    _string(payload["mode"], expected="deterministic_rules")
    _boolean(payload["openvino_available"], expected=False)
    _string(
        payload["warning"],
        expected="OpenVINO semantic inference is not enabled in v0.1.",
    )


def _health_inference(value: Any, *, require_openvino: bool) -> None:
    payload = _keys(value, {"mode", "openvino_available", "warning"})
    _string(payload["mode"], expected="deterministic_rules")
    available = _boolean(payload["openvino_available"])
    warning = _string(payload["warning"])
    expected_warning = (
        "OpenVINO embedding challenger is ready and remains opt-in."
        if available
        else "OpenVINO semantic inference is not enabled in v0.1."
    )
    if warning != expected_warning:
        raise GateError
    if require_openvino and not available:
        raise GateError


def _openvino_inference(value: Any) -> None:
    payload = _keys(
        value,
        {
            "chunks_processed",
            "device",
            "fallback_state",
            "mode",
            "model_id",
            "model_revision",
            "openvino_available",
        },
    )
    _integer(payload["chunks_processed"], minimum=1)
    _string(payload["device"], expected="CPU")
    _string(payload["fallback_state"], expected="not_used")
    _string(payload["mode"], expected="openvino_embedding")
    _string(payload["model_id"], expected="intfloat/multilingual-e5-small")
    _string(
        payload["model_revision"],
        expected="614241f622f53c4eeff9890bdc4f31cfecc418b3",
    )
    _boolean(payload["openvino_available"], expected=True)


def _findings(value: Any) -> None:
    if type(value) is not list:
        raise GateError
    for finding in value:
        payload = _keys(
            finding,
            {"action", "detector", "line", "severity", "source", "type"},
        )
        if _string(payload["action"]) not in {"ISOLATE", "PSEUDONYMIZE", "REDACT"}:
            raise GateError
        _string(payload["detector"])
        _integer(payload["line"], minimum=1)
        if _string(payload["severity"]) not in {"medium", "high", "critical"}:
            raise GateError
        _relative_source(payload["source"])
        _string(payload["type"])


def _safe_context(value: Any) -> tuple[list[dict[str, Any]], str | None, str]:
    payload = _keys(
        value,
        {"facts", "selection_method", "summary"},
        {"coverage_warning"},
    )
    if payload["summary"] is not None or type(payload["facts"]) is not list:
        raise GateError
    method = _string(payload["selection_method"])
    facts = payload["facts"]
    for index, fact in enumerate(facts, start=1):
        record = _keys(
            fact,
            {"id", "local_ref", "selection_score", "source", "text"},
        )
        match = _FACT_ID.fullmatch(_string(record["id"]))
        if match is None or int(match.group(1)) != index:
            raise GateError
        reference = _LOCAL_REF.fullmatch(_string(record["local_ref"]))
        if reference is None:
            raise GateError
        if reference.group(2) is not None and int(reference.group(2)) < int(reference.group(1)):
            raise GateError
        _integer(record["selection_score"])
        _relative_source(record["source"])
        _string(record["text"])

    warning: str | None = None
    if "coverage_warning" in payload:
        warning = _string(payload["coverage_warning"])
        if warning not in _COVERAGE_WARNINGS:
            raise GateError
    if facts and warning is not None:
        raise GateError
    return facts, warning, method


def _base_result(payload: dict[str, Any]) -> str:
    _string(payload["schema_version"], expected=SCHEMA_VERSION)
    decision = _string(payload["decision"])
    risk = _string(payload["risk_level"])
    if decision not in _DECISIONS or risk not in _RISKS:
        raise GateError
    _files(payload["files"])
    _security(payload["security"])
    return decision


def validate_success_payload(
    payload: dict[str, Any],
    *,
    command: str,
    require_openvino: bool = False,
) -> None:
    """Validate one parsed child result against the exact public v0.1 contract."""

    if command == "health":
        result = _keys(payload, {"commands", "inference", "schema_version", "status", "version"})
        _string(result["schema_version"], expected=SCHEMA_VERSION)
        _string(result["status"], expected="ok")
        _string(result["version"], expected="0.1.0")
        if result["commands"] != ["health", "scan", "analyze"]:
            raise GateError
        _health_inference(result["inference"], require_openvino=require_openvino)
        return

    if command == "scan":
        result = _keys(
            payload,
            {
                "decision",
                "files",
                "findings",
                "inference",
                "risk_level",
                "schema_version",
                "security",
            },
        )
        _base_result(result)
        _findings(result["findings"])
        _deterministic_inference(result["inference"])
        inspection = inspect_public_payload(result)
        if (
            inspection.raw_sensitive_spans_forwarded
            or inspection.untrusted_instruction_spans_forwarded
        ):
            raise GateError
        return

    if command != "analyze":
        raise GateError

    result = _keys(
        payload,
        {
            "decision",
            "efficiency",
            "files",
            "inference",
            "privacy",
            "risk_level",
            "safe_context",
            "schema_version",
            "security",
            "task",
        },
    )
    decision = _base_result(result)
    _string(result["task"])
    facts, warning, method = _safe_context(result["safe_context"])

    privacy = _keys(result["privacy"], {"raw_sensitive_spans_forwarded"})
    reported_sensitive_spans = _integer(
        privacy["raw_sensitive_spans_forwarded"],
        maximum=0,
    )
    inspection = inspect_public_payload(result)
    if (
        reported_sensitive_spans != inspection.raw_sensitive_spans_forwarded
        or inspection.raw_sensitive_spans_forwarded
        or inspection.untrusted_instruction_spans_forwarded
    ):
        raise GateError

    efficiency = _keys(
        result["efficiency"],
        {
            "capsule_tokens_estimated",
            "estimator",
            "original_tokens_estimated",
            "reduction_ratio",
        },
    )
    _integer(efficiency["capsule_tokens_estimated"])
    _string(efficiency["estimator"], expected="utf8_bytes_div_4_ceil_v1")
    _integer(efficiency["original_tokens_estimated"])
    # Tiny inputs can legitimately expand into a Capsule, so the reduction can
    # be negative; it must still be finite and can never exceed 100 percent.
    _number(efficiency["reduction_ratio"], maximum=1.0)

    if decision in {"BLOCK", "REQUIRE_CONFIRMATION"}:
        if facts or warning is None:
            raise GateError
        _deterministic_inference(result["inference"])
        if method != "deterministic_lexical_v1":
            raise GateError
        return

    if require_openvino:
        _openvino_inference(result["inference"])
        if method != "openvino_hybrid_relevance_v3":
            raise GateError
    elif method == "openvino_hybrid_relevance_v3":
        _openvino_inference(result["inference"])
    elif method == "deterministic_lexical_v1":
        _deterministic_inference(result["inference"])
    else:
        raise GateError


def validate_error_payload(payload: dict[str, Any]) -> None:
    """Allow only fixed, input-independent CLI error envelopes."""

    result = _keys(payload, {"error", "schema_version"})
    _string(result["schema_version"], expected=SCHEMA_VERSION)
    error = _keys(result["error"], {"code", "message"})
    code = _string(error["code"])
    message = _string(error["message"])
    if _ERRORS_BY_CODE.get(code) != message:
        raise GateError


def validate_serialized_response(
    serialized: str,
    *,
    kind: str,
    command: str | None = None,
    require_openvino: bool = False,
) -> str:
    """Validate and rebuild one canonical, allowlisted JSON response."""

    if len(serialized.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise GateError
    payload = _load(serialized)
    if kind == "error":
        validate_error_payload(payload)
    elif kind == "success" and command is not None:
        validate_success_payload(
            payload,
            command=command,
            require_openvino=require_openvino,
        )
    else:
        raise GateError
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--kind", choices=("success", "error"), required=True)
    parser.add_argument("--command", choices=("health", "scan", "analyze"))
    parser.add_argument("--require-openvino", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        namespace = _parser().parse_args(argv)
        raw = sys.stdin.buffer.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise GateError
        serialized = raw.decode("utf-8")
        canonical = validate_serialized_response(
            serialized,
            kind=namespace.kind,
            command=namespace.command,
            require_openvino=namespace.require_openvino,
        )
    except (GateError, UnicodeError):
        return 1
    sys.stdout.write(canonical + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
