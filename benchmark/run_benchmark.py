#!/usr/bin/env python3
"""Black-box acceptance and benchmark runner for AI Airlock.

The runner invokes only the public CLI and evaluates JSON output. It does not
import Airlock detectors, rankers, pipeline code, or OpenVINO implementations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "benchmark"
DATASET_ROOT = BENCHMARK_ROOT / "datasets"
DEFAULT_OUTPUT_DIR = BENCHMARK_ROOT / "results"
VARIANTS_PATH = BENCHMARK_ROOT / "variants.json"

SECRET_API_VALUE = "sk-test-MY_SUPER_SECRET_982374_ABCDEF0123456789"
SECRET_PASSWORD_VALUE = "DO_NOT_LEAK_ME_445566"
INTEGRATOR_SECRET_VALUE = "INTEGRATOR_SECRET_X91Q7"
INTEGRATOR_PASSWORD_VALUE = "INTEGRATOR_PASSWORD_4AB92"
SECRET_MARKERS = (
    SECRET_API_VALUE,
    "MY_SUPER_SECRET_982374",
    SECRET_PASSWORD_VALUE,
    INTEGRATOR_SECRET_VALUE,
    INTEGRATOR_PASSWORD_VALUE,
)
SECRET_FINDING_TYPES = frozenset(
    {
        "API_KEY",
        "AWS_ACCESS_KEY",
        "BEARER_TOKEN",
        "CONNECTION_STRING",
        "DATABASE_URL",
        "JWT",
        "PASSWORD",
        "PRIVATE_KEY",
    }
)
BENCHMARK_TOKEN_ESTIMATOR = "utf8_bytes_div_4_ceil_v1"
INJECTION_MIN_PRECISION = 0.80
INJECTION_MIN_RECALL = 0.90

_CAPSULE_DECISIONS = frozenset({"ALLOW", "ALLOW_WITH_TRANSFORM", "BLOCK"})
_CAPSULE_RISK_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
_SECURITY_FIELDS = frozenset(
    {
        "api_keys",
        "bearer_tokens",
        "jwt_tokens",
        "aws_keys",
        "private_keys",
        "database_credentials",
        "password_assignments",
        "emails",
        "phones",
        "chinese_ids",
        "ip_addresses",
        "pii_items",
        "prompt_injections",
        "data_exfiltration_attempts",
        "blocked_instructions",
    }
)


class BenchmarkError(RuntimeError):
    """Stable benchmark configuration or execution failure."""


@dataclass(frozen=True, slots=True)
class VariantSpec:
    name: str
    enabled: bool
    command: tuple[str, ...]
    subcommand_arguments: tuple[str, ...]
    arguments_by_command: tuple[tuple[str, tuple[str, ...]], ...]
    environment: tuple[tuple[str, str], ...]
    expected_modes_by_command: tuple[tuple[str, tuple[str, ...]], ...]
    requires_openvino_available: bool
    unavailable_reason: str | None

    def arguments_for(self, command: str) -> tuple[str, ...]:
        return dict(self.arguments_by_command).get(command, ())

    def expected_modes_for(self, command: str) -> tuple[str, ...]:
        return dict(self.expected_modes_by_command).get(command, ())


@dataclass(frozen=True, slots=True)
class CliRun:
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any] | None
    latency_ms: float


class BlackBoxClient:
    """Invoke one Airlock CLI variant without importing its implementation."""

    def __init__(self, spec: VariantSpec) -> None:
        self.spec = spec
        self.latencies_ms: list[float] = []

    def run(self, arguments: list[str], *, timeout_seconds: int = 60) -> CliRun:
        if not arguments:
            raise BenchmarkError("CLI arguments cannot be empty")
        command = [
            *self.spec.command,
            arguments[0],
            *self.spec.subcommand_arguments,
            *self.spec.arguments_for(arguments[0]),
            *arguments[1:],
        ]
        environment = os.environ.copy()
        environment.update(dict(self.spec.environment))
        # The benchmark consumes UTF-8 JSON regardless of the Windows runner's
        # active ANSI code page. Keep every child CLI on that byte contract.
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        started = perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
            latency_ms = (perf_counter() - started) * 1000
            payload = _parse_single_json(completed.stdout) if completed.returncode == 0 else None
            result = CliRun(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                payload=payload,
                latency_ms=latency_ms,
            )
        except (OSError, subprocess.TimeoutExpired):
            latency_ms = (perf_counter() - started) * 1000
            result = CliRun(
                returncode=127,
                stdout="",
                stderr="",
                payload=None,
                latency_ms=latency_ms,
            )
        self.latencies_ms.append(result.latency_ms)
        return result


def _parse_single_json(stdout: str) -> dict[str, Any] | None:
    if not stdout or stdout.count("\n") > 1:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkError(f"Unable to load benchmark data: {path.name}") from error
    if not isinstance(payload, dict):
        raise BenchmarkError(f"Benchmark data must be an object: {path.name}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _git_provenance() -> tuple[str | None, bool | None]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None, None
    if len(revision) != 40 or any(character not in "0123456789abcdef" for character in revision):
        return None, None
    return revision, status == ""


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _provenance(generated_at: str) -> dict[str, Any]:
    revision, worktree_clean = _git_provenance()
    inputs = [VARIANTS_PATH, *sorted(DATASET_ROOT.glob("*.json")), Path(__file__).resolve()]
    return {
        "run_id": f"{generated_at}-{revision[:12] if revision else 'no-git'}",
        "git_revision": revision,
        "git_worktree_clean": worktree_clean,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": {
            name: _package_version(name)
            for name in (
                "PyYAML",
                "numpy",
                "openvino",
                "openvino-genai",
                "openvino-tokenizers",
                "transformers",
            )
        },
        "inputs_sha256": {path.relative_to(ROOT).as_posix(): _sha256(path) for path in inputs},
    }


def _load_variants() -> dict[str, VariantSpec]:
    raw = _load_json(VARIANTS_PATH).get("variants")
    if not isinstance(raw, dict):
        raise BenchmarkError("variants.json is missing the variants object")
    variants: dict[str, VariantSpec] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not isinstance(value, dict):
            raise BenchmarkError("Invalid variant entry")
        command = value.get("command", [])
        subcommand_arguments = value.get("subcommand_arguments", [])
        arguments_by_command = value.get("arguments_by_command", {})
        environment = value.get("environment", {})
        modes_by_command = value.get("expected_modes_by_command", {})
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise BenchmarkError(f"Invalid command for variant {name}")
        if not isinstance(subcommand_arguments, list) or not all(
            isinstance(item, str) for item in subcommand_arguments
        ):
            raise BenchmarkError(f"Invalid subcommand arguments for variant {name}")
        if not isinstance(arguments_by_command, dict) or not all(
            isinstance(key, str)
            and isinstance(items, list)
            and all(isinstance(item, str) for item in items)
            for key, items in arguments_by_command.items()
        ):
            raise BenchmarkError(f"Invalid command-specific arguments for variant {name}")
        if not isinstance(modes_by_command, dict) or not all(
            isinstance(key, str)
            and isinstance(items, list)
            and all(isinstance(item, str) for item in items)
            for key, items in modes_by_command.items()
        ):
            raise BenchmarkError(f"Invalid command-specific inference modes for variant {name}")
        if not isinstance(environment, dict) or not all(
            isinstance(key, str) and isinstance(item, str) for key, item in environment.items()
        ):
            raise BenchmarkError(f"Invalid environment for variant {name}")
        materialized = tuple(
            item.replace("{python}", sys.executable).replace("{project_root}", str(ROOT))
            for item in command
        )
        variants[name] = VariantSpec(
            name=name,
            enabled=value.get("enabled") is True,
            command=materialized,
            subcommand_arguments=tuple(subcommand_arguments),
            arguments_by_command=tuple(
                sorted((key, tuple(items)) for key, items in arguments_by_command.items())
            ),
            environment=tuple(sorted(environment.items())),
            expected_modes_by_command=tuple(
                sorted((key, tuple(items)) for key, items in modes_by_command.items())
            ),
            requires_openvino_available=value.get("requires_openvino_available") is True,
            unavailable_reason=(
                value.get("unavailable_reason")
                if isinstance(value.get("unavailable_reason"), str)
                else None
            ),
        )
    return variants


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _estimate_tokens(value: str | bytes) -> int:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return (len(payload) + 3) // 4


def _inference_mode(payload: dict[str, Any] | None) -> str | None:
    if payload is None or not isinstance(payload.get("inference"), dict):
        return None
    mode = payload["inference"].get("mode")
    return mode if isinstance(mode, str) else None


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 3)


def _contains_any(haystack: str, needles: list[str] | tuple[str, ...]) -> bool:
    folded = haystack.casefold()
    return any(needle.casefold() in folded for needle in needles)


def _count_present_values(surfaces: list[str], values: list[str] | tuple[str, ...]) -> int:
    combined = "\n".join(surfaces).casefold()
    return sum(value.casefold() in combined for value in values)


def _flagship_forbidden_values(expected: dict[str, Any], incident_path: Path) -> list[str]:
    values = {
        value for value in expected.get("forbidden_content", []) if isinstance(value, str) and value
    }
    environment_path = incident_path / ".env.example"
    if environment_path.exists():
        for line in environment_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            value = line.split("=", 1)[1].strip()
            if value:
                values.add(value)
    customers_path = incident_path / "customers.csv"
    if customers_path.exists():
        with customers_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                for field in ("email", "phone"):
                    value = (row.get(field) or "").strip()
                    if value:
                        values.add(value)
    return sorted(values)


def _valid_capsule_structure(payload: dict[str, Any] | None) -> bool:
    if payload is None:
        return False
    required_top_level = {
        "schema_version",
        "task",
        "decision",
        "risk_level",
        "files",
        "safe_context",
        "security",
        "privacy",
        "efficiency",
        "inference",
    }
    if not required_top_level.issubset(payload):
        return False
    if (
        payload.get("schema_version") != "0.1"
        or not isinstance(payload.get("task"), str)
        or not payload["task"].strip()
        or payload.get("decision") not in _CAPSULE_DECISIONS
        or payload.get("risk_level") not in _CAPSULE_RISK_LEVELS
    ):
        return False

    def nonnegative_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    files = payload.get("files")
    if not isinstance(files, dict) or not all(
        nonnegative_int(files.get(name)) for name in ("inspected", "skipped", "total_bytes")
    ):
        return False

    security = payload.get("security")
    if not isinstance(security, dict) or not _SECURITY_FIELDS.issubset(security):
        return False
    if not all(nonnegative_int(security.get(name)) for name in _SECURITY_FIELDS):
        return False

    safe_context = payload.get("safe_context")
    if (
        not isinstance(safe_context, dict)
        or safe_context.get("summary") is not None
        or not isinstance(safe_context.get("facts"), list)
        or not isinstance(safe_context.get("selection_method"), str)
        or not safe_context["selection_method"]
    ):
        return False
    if "coverage_warning" in safe_context and not isinstance(
        safe_context.get("coverage_warning"), str
    ):
        return False
    for fact in safe_context["facts"]:
        if not isinstance(fact, dict):
            return False
        if not all(
            isinstance(fact.get(name), str) and bool(fact[name])
            for name in ("id", "text", "source", "local_ref")
        ):
            return False
        if not nonnegative_int(fact.get("selection_score")):
            return False

    privacy = payload.get("privacy")
    if not isinstance(privacy, dict) or not nonnegative_int(
        privacy.get("raw_sensitive_spans_forwarded")
    ):
        return False

    efficiency = payload.get("efficiency")
    if not isinstance(efficiency, dict):
        return False
    if not all(
        nonnegative_int(efficiency.get(name))
        for name in ("original_tokens_estimated", "capsule_tokens_estimated")
    ):
        return False
    reduction = efficiency.get("reduction_ratio")
    if (
        not isinstance(reduction, (int, float))
        or isinstance(reduction, bool)
        or not math.isfinite(float(reduction))
        or efficiency.get("estimator") != BENCHMARK_TOKEN_ESTIMATOR
    ):
        return False

    inference = payload.get("inference")
    if (
        not isinstance(inference, dict)
        or not isinstance(inference.get("mode"), str)
        or not isinstance(inference.get("openvino_available"), bool)
    ):
        return False
    if inference["mode"] == "openvino_embedding":
        if (
            inference["openvino_available"] is not True
            or not all(
                isinstance(inference.get(name), str) and bool(inference[name])
                for name in ("device", "model_id", "model_revision")
            )
            or not nonnegative_int(inference.get("chunks_processed"))
            or inference.get("fallback_state") != "not_used"
        ):
            return False
    elif inference["mode"] == "deterministic_rules":
        if inference["openvino_available"] is not False:
            return False
    else:
        return False
    return True


def _fact_text(payload: dict[str, Any]) -> str:
    safe_context = payload.get("safe_context", {})
    facts = safe_context.get("facts", []) if isinstance(safe_context, dict) else []
    return "\n".join(str(fact.get("text", "")) for fact in facts if isinstance(fact, dict))


def _evaluate_flagship(
    client: BlackBoxClient, *, expected_modes: tuple[str, ...]
) -> dict[str, Any]:
    expected = _load_json(DATASET_ROOT / "flagship_incident.json")
    incident_path = ROOT / str(expected["path"])
    forbidden_values = _flagship_forbidden_values(expected, incident_path)
    with tempfile.TemporaryDirectory(prefix="airlock-benchmark-flagship-") as temp_dir:
        audit_path = Path(temp_dir) / "audit.jsonl"
        run = client.run(
            [
                "analyze",
                "--task",
                str(expected["task"]),
                "--path",
                str(incident_path),
                "--audit-log",
                str(audit_path),
                "--json",
            ]
        )
        audit_text = audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""

    payload = run.payload or {}
    text = _fact_text(payload)
    fact_checks = {
        str(item["id"]): _contains_any(text, list(item["match_any"]))
        for item in expected["required_facts"]
    }
    security = payload.get("security", {}) if isinstance(payload.get("security"), dict) else {}
    security_checks = {
        key: isinstance(security.get(key), int) and security[key] >= minimum
        for key, minimum in expected["required_security_minimums"].items()
    }
    forbidden_count = _count_present_values(
        [run.stdout, run.stderr, audit_text],
        forbidden_values,
    )
    privacy = payload.get("privacy", {}) if isinstance(payload.get("privacy"), dict) else {}
    efficiency = (
        payload.get("efficiency", {}) if isinstance(payload.get("efficiency"), dict) else {}
    )
    inference = payload.get("inference", {}) if isinstance(payload.get("inference"), dict) else {}
    raw_bytes = sum(len(path.read_bytes()) for path in incident_path.iterdir() if path.is_file())
    raw_chars = sum(
        len(path.read_text(encoding="utf-8")) for path in incident_path.iterdir() if path.is_file()
    )
    capsule_text = run.stdout.rstrip("\n")
    raw_tokens = (raw_bytes + 3) // 4
    capsule_tokens = _estimate_tokens(capsule_text)
    reduction_ratio = round(1 - capsule_tokens / raw_tokens, 6) if raw_tokens else None
    cli_metrics_match = (
        efficiency.get("original_tokens_estimated") == raw_tokens
        and efficiency.get("capsule_tokens_estimated") == capsule_tokens
        and efficiency.get("reduction_ratio") == reduction_ratio
    )
    context = {
        "measurement_source": "benchmark_computed_from_cli_io",
        "raw_chars": raw_chars,
        "raw_bytes": raw_bytes,
        "raw_tokens_estimated": raw_tokens,
        "capsule_chars": len(capsule_text),
        "capsule_bytes": len(capsule_text.encode("utf-8")),
        "capsule_tokens_estimated": capsule_tokens,
        "context_reduction_ratio": reduction_ratio,
        "token_estimator": BENCHMARK_TOKEN_ESTIMATOR,
        "cli_reported_metrics_match": cli_metrics_match,
    }
    checks = {
        "cli_exit_zero": run.returncode == 0,
        "stderr_empty": run.stderr == "",
        "valid_json_structure": _valid_capsule_structure(run.payload),
        "decision_matches": payload.get("decision") == expected["expected_decision"],
        "inference_mode_matches_variant": inference.get("mode") in expected_modes,
        "context_metrics_independently_verified": cli_metrics_match,
        "required_facts_retained": all(fact_checks.values()),
        "security_minimums_met": all(security_checks.values()),
        "forbidden_content_absent": forbidden_count == 0,
        "raw_sensitive_spans_forwarded_zero": privacy.get("raw_sensitive_spans_forwarded") == 0,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "required_facts": fact_checks,
        "security_minimums": security_checks,
        "forbidden_values_tested": len(forbidden_values),
        "forbidden_value_count_found": forbidden_count,
        "context": context,
        "inference": {
            key: inference[key]
            for key in (
                "mode",
                "openvino_available",
                "device",
                "model_id",
                "model_revision",
                "chunks_processed",
                "fallback_state",
            )
            if key in inference
        },
        "latency_ms": round(run.latency_ms, 3),
    }


def _classification_metrics(
    expected_positive: set[str], predicted_positive: set[str], universe: set[str]
) -> dict[str, Any]:
    true_positive = len(expected_positive & predicted_positive)
    false_positive = len((universe - expected_positive) & predicted_positive)
    false_negative = len(expected_positive - predicted_positive)
    true_negative = len((universe - expected_positive) - predicted_positive)
    return {
        "tp": true_positive,
        "fp": false_positive,
        "tn": true_negative,
        "fn": false_negative,
        "precision": _ratio(true_positive, true_positive + false_positive),
        "recall": _ratio(true_positive, true_positive + false_negative),
    }


def _evaluate_secret_invariant(
    client: BlackBoxClient,
    *,
    expected_scan_modes: tuple[str, ...],
    expected_analyze_modes: tuple[str, ...],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="airlock-benchmark-secret-") as temp_dir:
        root = Path(temp_dir)
        workspace = root / "workspace"
        workspace.mkdir()
        positive_sources = {
            ".env",
            "api_key.log",
            "application.yaml",
            "database_password.log",
            "ordinary.txt",
            "service.log",
        }
        negative_sources = {"readme.txt", "limits.txt"}
        (workspace / "api_key.log").write_text(
            f"ERROR synthetic auth failure\nPAYMENTS_API_KEY={SECRET_API_VALUE}\n",
            encoding="utf-8",
        )
        (workspace / "database_password.log").write_text(
            f"ERROR database auth failure\nDB_PASSWORD={SECRET_PASSWORD_VALUE}\n",
            encoding="utf-8",
        )
        (workspace / ".env").write_text(
            f"PAYMENTS_API_KEY={INTEGRATOR_SECRET_VALUE}\n",
            encoding="utf-8",
        )
        (workspace / "application.yaml").write_text(
            f"database_password: {INTEGRATOR_PASSWORD_VALUE}\n",
            encoding="utf-8",
        )
        (workspace / "service.log").write_text(
            f"ERROR payment auth failure api_key={INTEGRATOR_SECRET_VALUE}\n",
            encoding="utf-8",
        )
        (workspace / "ordinary.txt").write_text(
            "ERROR payment failed. Emergency secret is "
            f"{INTEGRATOR_SECRET_VALUE}; database password is "
            f"{INTEGRATOR_PASSWORD_VALUE}.\n",
            encoding="utf-8",
        )
        (workspace / "readme.txt").write_text(
            "Store API credentials in the approved secret manager.\n",
            encoding="utf-8",
        )
        (workspace / "limits.txt").write_text(
            "The password retry limit is three attempts.\n",
            encoding="utf-8",
        )
        audit_path = root / "audit.jsonl"
        scan_run = client.run(["scan", "--path", str(workspace), "--json"])
        analyze_run = client.run(
            [
                "analyze",
                "--task",
                "Analyze the synthetic authentication failures.",
                "--path",
                str(workspace),
                "--audit-log",
                str(audit_path),
                "--json",
            ]
        )
        audit_text = audit_path.read_text(encoding="utf-8") if audit_path.exists() else ""

        error_workspace = root / "error-workspace"
        error_workspace.mkdir()
        (error_workspace / "corrupt.log").write_bytes(
            f"API_KEY={INTEGRATOR_SECRET_VALUE}".encode() + b"\xff"
        )
        error_run = client.run(["scan", "--path", str(error_workspace), "--json"])

    scan_payload = scan_run.payload or {}
    findings = scan_payload.get("findings", [])
    predicted_sources = {
        str(finding.get("source"))
        for finding in findings
        if isinstance(finding, dict) and finding.get("type") in SECRET_FINDING_TYPES
    }
    universe = positive_sources | negative_sources
    detection = _classification_metrics(positive_sources, predicted_sources, universe)
    surfaces = [
        scan_run.stdout,
        scan_run.stderr,
        analyze_run.stdout,
        analyze_run.stderr,
        audit_text,
        error_run.stdout,
        error_run.stderr,
    ]
    leaked_value_count = _count_present_values(surfaces, SECRET_MARKERS)
    payload = analyze_run.payload or {}
    privacy = payload.get("privacy", {}) if isinstance(payload.get("privacy"), dict) else {}
    try:
        audit_event = json.loads(audit_text.splitlines()[-1]) if audit_text else {}
    except json.JSONDecodeError:
        audit_event = {}
    checks = {
        "scan_exit_zero": scan_run.returncode == 0,
        "analyze_exit_zero": analyze_run.returncode == 0,
        "scan_inference_mode_matches_variant": (
            _inference_mode(scan_run.payload) in expected_scan_modes
        ),
        "analyze_inference_mode_matches_variant": (
            _inference_mode(analyze_run.payload) in expected_analyze_modes
        ),
        "controlled_error_exit_one": error_run.returncode == 1,
        "controlled_error_has_no_stdout": error_run.stdout == "",
        "secret_precision_one": detection["precision"] == 1.0,
        "secret_recall_one": detection["recall"] == 1.0,
        "raw_sensitive_spans_forwarded_zero": privacy.get("raw_sensitive_spans_forwarded") == 0,
        "audit_inference_mode_matches_variant": (
            isinstance(audit_event, dict)
            and audit_event.get("inference_mode") == _inference_mode(analyze_run.payload)
        ),
        "secret_leakage_zero": leaked_value_count == 0,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "classification": detection,
        "expected_secret_values": len(positive_sources),
        "forbidden_markers_tested": len(SECRET_MARKERS),
        "secret_leakage_count": leaked_value_count,
        "surfaces_checked": [
            "scan_stdout",
            "scan_stderr",
            "capsule_stdout",
            "capsule_stderr",
            "audit_log",
            "controlled_error_stdout",
            "controlled_error_stderr",
        ],
    }


def _evaluate_injection(
    client: BlackBoxClient, *, smoke: bool, expected_modes: tuple[str, ...]
) -> dict[str, Any]:
    dataset = _load_json(DATASET_ROOT / "injection_cases.json")
    raw_cases = dataset.get("cases", [])
    if not isinstance(raw_cases, list):
        raise BenchmarkError("injection_cases.json is missing cases")
    cases = raw_cases
    if smoke:
        malicious = [case for case in raw_cases if case.get("label") == "malicious"][:4]
        benign = [case for case in raw_cases if case.get("label") == "benign"][:4]
        cases = [*malicious, *benign]

    expected_positive: set[str] = set()
    predicted_positive: set[str] = set()
    universe: set[str] = set()
    case_results: list[dict[str, Any]] = []
    invocation_failures = 0
    for case in cases:
        case_id = str(case["id"])
        universe.add(case_id)
        if case.get("label") == "malicious":
            expected_positive.add(case_id)
        with tempfile.TemporaryDirectory(prefix="airlock-benchmark-injection-") as temp_dir:
            case_path = Path(temp_dir) / "case.txt"
            case_path.write_text(str(case["text"]), encoding="utf-8")
            run = client.run(["scan", "--path", str(case_path), "--json"])
        payload = run.payload or {}
        security = payload.get("security", {}) if isinstance(payload.get("security"), dict) else {}
        predicted = (
            int(security.get("prompt_injections", 0)) > 0
            or int(security.get("data_exfiltration_attempts", 0)) > 0
        )
        if predicted:
            predicted_positive.add(case_id)
        invocation_valid = (
            run.returncode == 0
            and run.payload is not None
            and _inference_mode(run.payload) in expected_modes
        )
        invocation_failures += not invocation_valid
        case_results.append(
            {
                "id": case_id,
                "category": case.get("category"),
                "expected": case.get("label"),
                "predicted": "malicious" if predicted else "benign",
                "correct": predicted == (case.get("label") == "malicious"),
                "invocation_valid": invocation_valid,
            }
        )

    metrics = _classification_metrics(expected_positive, predicted_positive, universe)
    quality_checks = {
        "precision_at_least_threshold": metrics["precision"] >= INJECTION_MIN_PRECISION,
        "recall_at_least_threshold": metrics["recall"] >= INJECTION_MIN_RECALL,
    }
    return {
        "status": "MEASURED" if invocation_failures == 0 else "ERROR",
        "cases_evaluated": len(cases),
        "dataset_cases": len(raw_cases),
        "smoke_subset": smoke,
        "invocation_failures": invocation_failures,
        "classification": metrics,
        "quality_gate": {
            "pass": invocation_failures == 0 and all(quality_checks.values()),
            "minimum_precision": INJECTION_MIN_PRECISION,
            "minimum_recall": INJECTION_MIN_RECALL,
            "checks": quality_checks,
        },
        "cases": case_results,
    }


def _selected_sources(payload: dict[str, Any]) -> list[str]:
    safe_context = payload.get("safe_context", {})
    facts = safe_context.get("facts", []) if isinstance(safe_context, dict) else []
    output: list[str] = []
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("source"), str):
            continue
        source = Path(fact["source"]).stem
        if source not in output:
            output.append(source)
    return output


def _evaluate_relevance(
    client: BlackBoxClient, *, smoke: bool, expected_modes: tuple[str, ...]
) -> dict[str, Any]:
    dataset = _load_json(DATASET_ROOT / "relevance_cases.json")
    raw_tasks = dataset.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise BenchmarkError("relevance_cases.json is missing tasks")
    tasks = raw_tasks[:2] if smoke else raw_tasks
    case_results: list[dict[str, Any]] = []
    recalls: list[float] = []
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    cross_lingual_recalls: list[float] = []
    raw_chars_total = 0
    raw_tokens_total = 0
    capsule_chars_total = 0
    capsule_tokens_total = 0
    invocation_failures = 0

    for task_case in tasks:
        chunks = task_case.get("chunks", [])
        if not isinstance(chunks, list):
            raise BenchmarkError(f"Invalid chunks for {task_case.get('id')}")
        with tempfile.TemporaryDirectory(prefix="airlock-benchmark-relevance-") as temp_dir:
            workspace = Path(temp_dir)
            for chunk in chunks:
                (workspace / str(chunk["source"])).write_text(str(chunk["text"]), encoding="utf-8")
            run = client.run(
                [
                    "analyze",
                    "--task",
                    str(task_case["task"]),
                    "--path",
                    str(workspace),
                    "--json",
                ]
            )

        invocation_valid = (
            run.returncode == 0
            and _valid_capsule_structure(run.payload)
            and _inference_mode(run.payload) in expected_modes
        )
        invocation_failures += not invocation_valid
        payload = run.payload or {}
        selected = _selected_sources(payload)
        relevant = {str(chunk["id"]) for chunk in chunks if chunk.get("label") == "relevant"}
        k = int(task_case.get("recommended_k", 4))
        top_k = selected[:k]
        retained = len(relevant & set(top_k))
        recall = retained / len(relevant) if relevant else 0.0
        precision = retained / len(top_k) if top_k else 0.0
        first_rank = next(
            (index for index, value in enumerate(selected, 1) if value in relevant), None
        )
        reciprocal_rank = 1 / first_rank if first_rank is not None else 0.0
        recalls.append(recall)
        precisions.append(precision)
        reciprocal_ranks.append(reciprocal_rank)
        if task_case.get("cross_lingual") is True:
            cross_lingual_recalls.append(recall)

        raw_chars = sum(len(str(chunk["text"])) for chunk in chunks)
        raw_bytes = sum(len(str(chunk["text"]).encode("utf-8")) for chunk in chunks)
        capsule_text = run.stdout.rstrip("\n")
        raw_chars_total += raw_chars
        raw_tokens_total += (raw_bytes + 3) // 4
        capsule_chars_total += len(capsule_text)
        capsule_tokens_total += _estimate_tokens(capsule_text)
        case_results.append(
            {
                "id": task_case["id"],
                "task_language": task_case.get("task_language"),
                "cross_lingual": task_case.get("cross_lingual") is True,
                "k": k,
                "relevant_total": len(relevant),
                "selected_at_k": len(top_k),
                "relevant_retained_at_k": retained,
                "recall_at_k": round(recall, 6),
                "precision_at_k": round(precision, 6),
                "reciprocal_rank": round(reciprocal_rank, 6),
                "invocation_valid": invocation_valid,
            }
        )

    return {
        "status": "MEASURED" if invocation_failures == 0 else "ERROR",
        "tasks_evaluated": len(tasks),
        "dataset_tasks": len(raw_tasks),
        "smoke_subset": smoke,
        "invocation_failures": invocation_failures,
        "mean_recall_at_k": _mean(recalls),
        "mean_precision_at_k": _mean(precisions),
        "mean_reciprocal_rank": _mean(reciprocal_ranks),
        "cross_lingual_mean_recall_at_k": _mean(cross_lingual_recalls),
        "context": {
            "measurement_scope": "relevance_micro_fixtures_not_primary_efficiency_claim",
            "raw_chars": raw_chars_total,
            "raw_tokens_estimated": raw_tokens_total,
            "capsule_chars": capsule_chars_total,
            "capsule_tokens_estimated": capsule_tokens_total,
            "context_reduction_ratio": (
                round(1 - capsule_tokens_total / raw_tokens_total, 6) if raw_tokens_total else None
            ),
        },
        "cases": case_results,
    }


def _performance(client: BlackBoxClient) -> dict[str, Any]:
    values = client.latencies_ms
    return {
        "cli_invocations": len(values),
        "total_latency_ms": round(sum(values), 3),
        "mean_latency_ms": round(statistics.fmean(values), 3) if values else None,
        "p50_latency_ms": _percentile(values, 0.50),
        "p95_latency_ms": _percentile(values, 0.95),
    }


def _unavailable_variant(spec: VariantSpec, reason: str | None = None) -> dict[str, Any]:
    return {
        "status": "NOT_AVAILABLE",
        "reason": reason or spec.unavailable_reason or "Variant is not configured.",
    }


def _run_variant(spec: VariantSpec, *, smoke: bool) -> dict[str, Any]:
    if not spec.enabled or not spec.command:
        return _unavailable_variant(spec)
    client = BlackBoxClient(spec)
    health = client.run(["health", "--json"])
    if health.returncode != 0 or health.payload is None:
        return _unavailable_variant(spec, "CLI health check failed.")
    raw_inference = health.payload.get("inference", {})
    inference = raw_inference if isinstance(raw_inference, dict) else {}
    mode = inference.get("mode")
    expected_health_modes = spec.expected_modes_for("health")
    if expected_health_modes and mode not in expected_health_modes:
        return _unavailable_variant(
            spec,
            "Observed inference mode does not match the registered variant.",
        )
    if spec.requires_openvino_available and inference.get("openvino_available") is not True:
        return _unavailable_variant(spec)

    expected_scan_modes = spec.expected_modes_for("scan")
    expected_analyze_modes = spec.expected_modes_for("analyze")
    flagship = _evaluate_flagship(client, expected_modes=expected_analyze_modes)
    secrets = _evaluate_secret_invariant(
        client,
        expected_scan_modes=expected_scan_modes,
        expected_analyze_modes=expected_analyze_modes,
    )
    injection = _evaluate_injection(
        client,
        smoke=smoke,
        expected_modes=expected_scan_modes,
    )
    relevance = _evaluate_relevance(
        client,
        smoke=smoke,
        expected_modes=expected_analyze_modes,
    )
    gates = {
        "flagship_acceptance": flagship["status"] == "PASS",
        "secret_leakage_invariant": secrets["status"] == "PASS",
        "injection_benchmark_completed": injection["status"] == "MEASURED",
        "injection_quality": injection["quality_gate"]["pass"] is True,
        "relevance_benchmark_completed": relevance["status"] == "MEASURED",
    }
    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "inference": {
            "health_mode": mode,
            "openvino_available": inference.get("openvino_available") is True,
            "expected_scan_modes": list(expected_scan_modes),
            "expected_analyze_modes": list(expected_analyze_modes),
        },
        "acceptance_gates": gates,
        "security": {
            "secret_detection": secrets,
            "prompt_injection": injection,
            "secret_leakage_count": (
                secrets["secret_leakage_count"] + flagship["forbidden_value_count_found"]
            ),
        },
        "flagship": flagship,
        "relevance": relevance,
        "utility": {
            "flagship_required_facts": flagship["required_facts"],
            "required_facts_retained": sum(flagship["required_facts"].values()),
            "required_facts_total": len(flagship["required_facts"]),
            "flagship_task_pass": flagship["status"] == "PASS",
        },
        "context": flagship["context"],
        "performance": _performance(client),
    }


def _comparison(variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rules = variants.get("rules-only", {})
    openvino = variants.get("openvino", {})
    statuses = {rules.get("status"), openvino.get("status")}
    if "NOT_AVAILABLE" in statuses or None in statuses:
        return {
            "status": "NOT_AVAILABLE",
            "reason": "Both rules-only and OpenVINO variants must be registered and runnable.",
        }
    if rules.get("status") != "PASS" or openvino.get("status") != "PASS":
        return {
            "status": "INVALID",
            "reason": "A/B deltas are withheld because one or both variants failed acceptance gates.",
        }

    def delta(path: tuple[str, ...]) -> float | None:
        left: Any = rules
        right: Any = openvino
        for key in path:
            left = left.get(key) if isinstance(left, dict) else None
            right = right.get(key) if isinstance(right, dict) else None
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            return None
        return round(right - left, 6)

    return {
        "status": "MEASURED",
        "delta_openvino_minus_rules": {
            "mean_recall_at_k": delta(("relevance", "mean_recall_at_k")),
            "mean_precision_at_k": delta(("relevance", "mean_precision_at_k")),
            "context_reduction_ratio": delta(("context", "context_reduction_ratio")),
            "secret_leakage_count": delta(("security", "secret_leakage_count")),
            "total_latency_ms": delta(("performance", "total_latency_ms")),
        },
    }


def _render_markdown(report: dict[str, Any]) -> str:
    provenance = report["provenance"]
    lines = [
        "# AI Airlock Benchmark",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Run ID: `{provenance['run_id']}`",
        f"- Git revision: `{provenance['git_revision']}`",
        f"- Git worktree clean at start: `{provenance['git_worktree_clean']}`",
        f"- Python: `{provenance['python_version']}`",
        f"- Platform: `{provenance['platform']}`",
        f"- Scope: `{report['scope']}`",
        f"- Overall status: `{report['status']}`",
        "",
    ]
    for name, result in report["variants"].items():
        lines.extend((f"## Variant: {name}", "", f"Status: `{result['status']}`", ""))
        if result["status"] == "NOT_AVAILABLE":
            lines.extend((f"Reason: {result['reason']}", ""))
            continue
        secret = result["security"]["secret_detection"]
        injection = result["security"]["prompt_injection"]["classification"]
        relevance = result["relevance"]
        context = result["context"]
        utility = result["utility"]
        performance = result["performance"]
        inference = result["flagship"].get("inference", {})
        lines.extend(
            (
                "### Security",
                "",
                f"- Secret precision: `{secret['classification']['precision']}`",
                f"- Secret recall: `{secret['classification']['recall']}`",
                f"- Secret leakage count: `{result['security']['secret_leakage_count']}`",
                f"- Injection TP/FP/TN/FN: `{injection['tp']}/{injection['fp']}/"
                f"{injection['tn']}/{injection['fn']}`",
                f"- Injection precision: `{injection['precision']}`",
                f"- Injection recall: `{injection['recall']}`",
                "",
                "### Relevance",
                "",
                f"- Mean Recall@K: `{relevance['mean_recall_at_k']}`",
                f"- Mean Precision@K: `{relevance['mean_precision_at_k']}`",
                f"- MRR: `{relevance['mean_reciprocal_rank']}`",
                f"- Cross-lingual mean Recall@K: `{relevance['cross_lingual_mean_recall_at_k']}`",
                "",
                "### Context and utility",
                "",
                f"- Raw tokens estimated: `{context['raw_tokens_estimated']}`",
                f"- Capsule tokens estimated: `{context['capsule_tokens_estimated']}`",
                f"- Context reduction ratio: `{context['context_reduction_ratio']}`",
                f"- Required facts retained: `{utility['required_facts_retained']}/"
                f"{utility['required_facts_total']}`",
                "- Flagship capsule acceptance: "
                f"`{'PASS' if utility['flagship_task_pass'] else 'FAIL'}`",
                "",
                "### Performance",
                "",
                f"- CLI invocations: `{performance['cli_invocations']}`",
                f"- Total latency: `{performance['total_latency_ms']} ms`",
                f"- Mean latency: `{performance['mean_latency_ms']} ms`",
                f"- P95 latency: `{performance['p95_latency_ms']} ms`",
                "",
            )
        )
        if inference.get("mode") == "openvino_embedding":
            lines.extend(
                (
                    "### OpenVINO provenance",
                    "",
                    f"- Model: `{inference.get('model_id')}`",
                    f"- Model revision: `{inference.get('model_revision')}`",
                    f"- Device: `{inference.get('device')}`",
                    f"- Mode: `{inference.get('mode')}`",
                    "",
                )
            )
    comparison = report.get("comparison", {})
    lines.extend(("## Rules-only vs OpenVINO", "", f"Status: `{comparison['status']}`", ""))
    if comparison["status"] != "MEASURED":
        lines.extend((f"Reason: {comparison['reason']}", ""))
    else:
        for metric, value in comparison["delta_openvino_minus_rules"].items():
            lines.append(f"- {metric}: `{value}`")
        lines.append("")
    return "\n".join(lines)


def _write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "latest.json"
    markdown_path = output_dir / "latest.md"
    json_text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    markdown_text = _render_markdown(report)
    flagship_expected = _load_json(DATASET_ROOT / "flagship_incident.json")
    flagship_path = ROOT / str(flagship_expected["path"])
    flagship_forbidden = _flagship_forbidden_values(flagship_expected, flagship_path)
    report_forbidden = [*SECRET_MARKERS]
    report_forbidden.extend(flagship_forbidden)
    if _count_present_values([json_text, markdown_text], report_forbidden):
        raise BenchmarkError("Generated report failed the secret leakage invariant")
    json_path.write_text(json_text, encoding="utf-8")
    markdown_path.write_text(markdown_text, encoding="utf-8")
    return json_path, markdown_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true", help="run the small CI acceptance set")
    mode.add_argument(
        "--compare",
        action="store_true",
        help="run registered rules-only and OpenVINO variants and compute A/B deltas",
    )
    parser.add_argument(
        "--variant",
        default="rules-only",
        help="registered variant to run when --compare is not used",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="directory for latest.json and latest.md",
    )
    parser.add_argument("--list-variants", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        registered = _load_variants()
        if arguments.list_variants:
            print("\n".join(sorted(registered)))
            return 0
        names = ["rules-only", "openvino"] if arguments.compare else [arguments.variant]
        missing = [name for name in names if name not in registered]
        if missing:
            raise BenchmarkError(f"Unknown benchmark variant: {missing[0]}")
        variants = {name: _run_variant(registered[name], smoke=arguments.smoke) for name in names}
        available_results = [
            result for result in variants.values() if result.get("status") in {"PASS", "FAIL"}
        ]
        unavailable_count = sum(
            result.get("status") == "NOT_AVAILABLE" for result in variants.values()
        )
        if not available_results:
            status = "NOT_AVAILABLE"
        elif any(result["status"] == "FAIL" for result in available_results):
            status = "FAIL"
        elif unavailable_count:
            status = "PARTIAL"
        else:
            status = "PASS"
        generated_at = datetime.now(UTC).isoformat(timespec="seconds")
        report = {
            "schema_version": "1.0",
            "benchmark_version": "0.1.0",
            "generated_at": generated_at,
            "provenance": _provenance(generated_at),
            "scope": "smoke" if arguments.smoke else "full",
            "status": status,
            "variants": variants,
            "comparison": _comparison(variants),
            "report_safety": {
                "known_fixture_forbidden_value_count": 0,
                "scope": "benchmark_secret_sentinels_and_flagship_raw_values",
                "pass": True,
            },
        }
        json_path, markdown_path = _write_report(report, arguments.output_dir.resolve())
        print(
            json.dumps(
                {
                    "status": status,
                    "json_report": str(json_path),
                    "markdown_report": str(markdown_path),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 1 if status == "FAIL" else 2 if status in {"NOT_AVAILABLE", "PARTIAL"} else 0
    except BenchmarkError as error:
        print(json.dumps({"status": "ERROR", "message": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
