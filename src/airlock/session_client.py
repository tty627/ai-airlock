"""Bounded Agent client: no raw-directory option and no remote endpoint support."""

from __future__ import annotations

import http.client
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from airlock.capsule.leak_guard import enforce_public_payload_is_safe
from airlock.errors import AirlockError
from airlock.serialization import stable_json
from airlock.session_server import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, PROTOCOL, parse_object


class ClientError(AirlockError):
    code = "SESSION_CLIENT_FAILED"
    public_message = "The local session response could not be validated."


def validate_response(payload: dict[str, Any], config: dict[str, Any], operation: str) -> None:
    common = {"schema_version", "case_id", "version", "status"}
    if (
        payload.get("schema_version") != PROTOCOL
        or payload.get("case_id") != config["case_id"]
        or payload.get("version") != config["version"]
    ):
        raise ClientError()
    if operation == "report":
        from airlock.report import render_report_markdown

        if set(payload) != common | {"report", "markdown"}:
            raise ClientError()
        if payload["status"] != "REPORT_VALIDATED":
            raise ClientError()
        if render_report_markdown(payload["report"]) != payload["markdown"]:
            raise ClientError()
    else:
        if set(payload) != common | {"round", "task", "safe_context", "budget", "inference"}:
            raise ClientError()
        if type(payload["round"]) is not int or not 0 <= payload["round"] <= 2:
            raise ClientError()
        if operation == "begin" and payload["round"] != 0:
            raise ClientError()
        if operation == "query" and payload["round"] == 0:
            raise ClientError()
        if not isinstance(payload["task"], str) or not payload["task"].strip():
            raise ClientError()
        context = payload["safe_context"]
        if not isinstance(context, dict) or set(context) != {"facts", "reference_scope"}:
            raise ClientError()
        if context["reference_scope"] != "sanitized_snapshot":
            raise ClientError()
        facts = context["facts"]
        if not isinstance(facts, list) or len(facts) > 8:
            raise ClientError()
        if payload["status"] != ("OK" if facts else "NO_NEW_EVIDENCE"):
            raise ClientError()
        ids = set()
        for fact in facts:
            if not isinstance(fact, dict) or set(fact) != {
                "id",
                "text",
                "source",
                "local_ref",
                "start_line",
                "end_line",
            }:
                raise ClientError()
            if any(
                not isinstance(fact[k], str) or not fact[k]
                for k in ("id", "text", "source", "local_ref")
            ):
                raise ClientError()
            if not re.fullmatch(r"evidence_[a-p]{24}", fact["id"]) or fact["id"] in ids:
                raise ClientError()
            ids.add(fact["id"])
            source = fact["source"]
            if (
                source.startswith("/")
                or "\\" in source
                or ":" in source
                or any(part in {"", ".", ".."} for part in source.split("/"))
            ):
                raise ClientError()
            start, end = fact["start_line"], fact["end_line"]
            if type(start) is not int or type(end) is not int or not 1 <= start <= end:
                raise ClientError()
            reference = f"L{start}" if start == end else f"L{start}-L{end}"
            if fact["local_ref"] != reference:
                raise ClientError()
        budget = payload["budget"]
        number_keys = {
            "round_tokens_estimated",
            "cumulative_tokens_estimated",
            "max_total_tokens",
            "max_followups",
            "rounds_used",
        }
        if not isinstance(budget, dict) or set(budget) != number_keys | {
            "token_estimator",
            "accounting_scope",
        }:
            raise ClientError()
        if any(type(budget[key]) is not int or budget[key] < 0 for key in number_keys):
            raise ClientError()
        if (
            budget["token_estimator"] != "utf8_bytes_div_4_ceil_v1"
            or budget["accounting_scope"] != "canonical_json_new_responses_retries_excluded"
            or not 0 <= budget["rounds_used"] == payload["round"] <= budget["max_followups"] <= 2
            or not 0
            < budget["round_tokens_estimated"]
            <= budget["cumulative_tokens_estimated"]
            <= budget["max_total_tokens"]
            <= 100000
        ):
            raise ClientError()
        from airlock.serialization import estimate_tokens

        if estimate_tokens(payload) != budget["round_tokens_estimated"]:
            raise ClientError()
        inference = payload["inference"]
        if config["relevance_backend"] == "lexical":
            expected = {
                "mode": "deterministic_lexical_v1",
                "openvino_available": False,
                "fallback_state": "not_used",
            }
        elif not facts and inference.get("mode") == "not_run":
            expected = {
                "mode": "not_run",
                "requested_backend": "openvino",
                "reason": "NO_NEW_EVIDENCE",
                "fallback_state": "not_used",
            }
        else:
            from airlock.relevance import openvino_inference_metadata

            chunks = inference.get("chunks_processed")
            if type(chunks) is not int or chunks <= 0:
                raise ClientError()
            expected = openvino_inference_metadata(chunks_processed=chunks)
        if inference != expected:
            raise ClientError()
    enforce_public_payload_is_safe(payload, ())


def read_bounded(path: Path, max_bytes: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ClientError()
    with path.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ClientError()
    return data


def request(connection_path: Path, operation: str, **fields: Any) -> dict[str, Any]:
    config = parse_object(read_bounded(connection_path, 4096))
    if set(config) != {
        "schema_version",
        "url",
        "bearer",
        "case_id",
        "version",
        "relevance_backend",
    }:
        raise ClientError()
    if config["schema_version"] != PROTOCOL:
        raise ClientError()
    if not all(isinstance(config[k], str) for k in ("url", "bearer", "case_id", "version")):
        raise ClientError()
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", config["bearer"]):
        raise ClientError()
    if config["relevance_backend"] not in {"lexical", "openvino"}:
        raise ClientError()
    url = urlsplit(config["url"])
    if (
        url.scheme != "http"
        or url.hostname != "127.0.0.1"
        or url.username is not None
        or url.password is not None
        or url.path
        or url.query
        or url.fragment
        or url.port is None
        or config["url"] != f"http://127.0.0.1:{url.port}"
    ):
        raise ClientError()
    allowed = {"begin": set(), "query": {"question", "request_id"}, "report": {"draft"}}
    if operation not in allowed or set(fields) != allowed[operation]:
        raise ClientError()
    body = stable_json(
        {
            "operation": operation,
            "case_id": config["case_id"],
            "version": config["version"],
            **fields,
        }
    ).encode("utf-8")
    if len(body) > MAX_REQUEST_BYTES:
        raise ClientError()
    # http.client never consults proxy environment variables or follows redirects.
    conn = http.client.HTTPConnection("127.0.0.1", url.port, timeout=120)
    try:
        conn.request(
            "POST",
            "/v1/session",
            body,
            {"Authorization": "Bearer " + config["bearer"], "Content-Type": "application/json"},
        )
        response = conn.getresponse()
        data = response.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES or response.status != 200:
            raise ClientError()
        if response.getheader("Content-Type") != "application/json; charset=utf-8":
            raise ClientError()
        payload = parse_object(data)
        validate_response(payload, config, operation)
        return payload
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    from airlock.cli import _SafeArgumentParser

    parser = _SafeArgumentParser(description=__doc__)
    parser.add_argument("--connection", required=True)
    commands = parser.add_subparsers(dest="operation", required=True)
    begin = commands.add_parser("begin")
    query = commands.add_parser("query")
    query.add_argument("--question", required=True)
    query.add_argument("--request-id", required=True)
    report = commands.add_parser("report")
    report.add_argument("--draft", required=True)
    for sub in (begin, query, report):
        sub.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
        fields: dict[str, Any] = {}
        if args.operation == "query":
            fields = {"question": args.question, "request_id": args.request_id}
        elif args.operation == "report":
            fields = {"draft": parse_object(read_bounded(Path(args.draft), MAX_REQUEST_BYTES))}
        result = request(Path(args.connection), args.operation, **fields)
        print(stable_json(result))
        return 0
    except Exception:
        print(
            stable_json(
                {
                    "schema_version": PROTOCOL,
                    "error": {"code": ClientError.code, "message": ClientError.public_message},
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
