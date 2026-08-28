"""Command-line contract for the deterministic AI Airlock MVP."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Any, NoReturn

from airlock.errors import AirlockError, RuntimeUnavailableError
from airlock.serialization import stable_json


class _UsageError(AirlockError):
    code = "INVALID_ARGUMENTS"
    public_message = "The command arguments are invalid."


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:  # noqa: ARG002
        raise _UsageError()


def health() -> dict[str, Any]:
    """Load the runtime inside ``main``'s safe exception boundary."""

    from airlock.pipeline import health as pipeline_health

    return pipeline_health()


def scan(**kwargs: Any) -> dict[str, Any]:
    """Load the runtime lazily so missing dependencies never expose a traceback."""

    from airlock.pipeline import scan as pipeline_scan

    return pipeline_scan(**kwargs)


def analyze(**kwargs: Any) -> dict[str, Any]:
    """Load the runtime lazily so missing dependencies never expose a traceback."""

    from airlock.pipeline import analyze as pipeline_analyze

    return pipeline_analyze(**kwargs)


def _add_output_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one compact JSON document on stdout",
    )


def _add_scan_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", required=True, help="local file or directory")
    parser.add_argument("--policy", help="strict YAML policy override")
    parser.add_argument("--audit-log", help="metadata-only JSONL path outside input")
    _add_output_flag(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(prog="ai-airlock")
    subparsers = parser.add_subparsers(dest="command", required=True)

    health_parser = subparsers.add_parser("health", help="report local mode and version")
    _add_output_flag(health_parser)

    scan_parser = subparsers.add_parser("scan", help="inventory local security findings")
    _add_scan_options(scan_parser)

    analyze_parser = subparsers.add_parser("analyze", help="compile task-conditioned safe context")
    analyze_parser.add_argument("--task", required=True, help="downstream user task")
    analyze_parser.add_argument(
        "--relevance-backend",
        choices=("lexical", "openvino"),
        default="lexical",
        help="explicit evidence selector; OpenVINO never falls back silently",
    )
    analyze_parser.add_argument(
        "--model-dir",
        help="prepared local OpenVINO model directory",
    )
    _add_scan_options(analyze_parser)
    return parser


def _human_report(command: str, result: dict[str, Any]) -> str:
    if command == "health":
        inference = result["inference"]
        return "\n".join(
            (
                "AI Airlock: ok",
                f"Version: {result['version']}",
                f"Mode: {inference['mode']}",
                f"OpenVINO available: {'yes' if inference['openvino_available'] else 'no'}",
            )
        )

    files = result["files"]
    security = result["security"]
    lines = [
        f"Decision: {result['decision']}",
        f"Risk: {result['risk_level']}",
        f"Files inspected: {files['inspected']}",
        f"Files skipped: {files['skipped']}",
        f"API keys: {security['api_keys']}",
        f"DB credentials: {security['database_credentials']}",
        f"PII items: {security['pii_items']}",
        f"Prompt injections: {security['prompt_injections']}",
        f"Data exfiltration attempts: {security['data_exfiltration_attempts']}",
    ]
    if command == "analyze":
        lines.append("Safe Context Capsule:")
        facts = result["safe_context"]["facts"]
        if not facts:
            lines.append(
                f"- {result['safe_context'].get('coverage_warning', 'NO_RELEVANT_CONTEXT')}"
            )
        for fact in facts:
            lines.append(f"- {fact['source']}:{fact['local_ref']} {fact['text']}")
    return "\n".join(lines)


def _emit_error(error: AirlockError, json_requested: bool) -> None:
    if json_requested:
        payload = {
            "schema_version": "0.1",
            "error": {"code": error.code, "message": error.public_message},
        }
        sys.stderr.write(stable_json(payload) + "\n")
    else:
        sys.stderr.write(f"ERROR {error.code}: {error.public_message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    json_requested = "--json" in arguments
    try:
        namespace = build_parser().parse_args(arguments)
        command = namespace.command
        if command == "health":
            result = health()
        elif command == "scan":
            result = scan(
                path=namespace.path,
                policy_path=namespace.policy,
                audit_log=namespace.audit_log,
            )
        else:
            result = analyze(
                task=namespace.task,
                path=namespace.path,
                policy_path=namespace.policy,
                audit_log=namespace.audit_log,
                relevance_backend=namespace.relevance_backend,
                model_dir=namespace.model_dir,
            )
        output = stable_json(result) if namespace.json else _human_report(command, result)
        sys.stdout.write(output + "\n")
        return 0
    except AirlockError as error:
        _emit_error(error, json_requested)
        return 1
    except ModuleNotFoundError:
        _emit_error(RuntimeUnavailableError(), json_requested)
        return 2
    except Exception:
        error = AirlockError()
        error.code = "INTERNAL_ERROR"
        _emit_error(error, json_requested)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
