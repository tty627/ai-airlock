"""Owner-started loopback broker for one immutable, sanitized evidence case.

The broker's bounded API is not an OS sandbox. Run the Agent under an identity
without access to the source directory when enforcing a raw-file boundary.
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from time import monotonic
from typing import Any

from airlock.capsule.leak_guard import enforce_public_payload_is_safe
from airlock.errors import AirlockError
from airlock.serialization import stable_json

PROTOCOL = "finals-session-v1"
MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Invalid JSON.")
        result[key] = value
    return result


def _invalid_constant(value: str) -> Any:
    raise ValueError("Invalid JSON.")


def parse_object(data: bytes) -> dict[str, Any]:
    value = json.loads(
        data.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant
    )
    if not isinstance(value, dict):
        raise ValueError("Invalid JSON.")
    return value


def error_response(code: str) -> dict[str, Any]:
    return {
        "schema_version": PROTOCOL,
        "error": {"code": code, "message": "The session request could not be completed safely."},
    }


class LoopbackSessionServer(HTTPServer):
    """Serial requests keep session and report publication in one critical path."""

    allow_reuse_address = False

    def __init__(self, session: Any) -> None:
        self.session = session
        self._bearer = secrets.token_urlsafe(32)
        self.request_count = 0
        super().__init__(("127.0.0.1", 0), _Handler)
        self.timeout = 1.0

    def connection_config(self) -> dict[str, Any]:
        return {
            "schema_version": PROTOCOL,
            "url": f"http://127.0.0.1:{self.server_port}",
            "bearer": self._bearer,
            "case_id": self.session.case_id,
            "version": self.session.version,
            "relevance_backend": self.session.relevance_backend,
        }

    def dispatch(self, body: dict[str, Any]) -> dict[str, Any]:
        operation = body.get("operation")
        common = {"operation", "case_id", "version"}
        expected = {
            "begin": common,
            "query": common | {"question", "request_id"},
            "report": common | {"draft"},
        }
        if not isinstance(operation, str) or operation not in expected:
            raise ValueError("Invalid request.")
        if set(body) != expected[operation]:
            raise ValueError("Invalid request.")
        if body["case_id"] != self.session.case_id or body["version"] != self.session.version:
            raise ValueError("Invalid request.")
        if operation == "begin":
            return self.session.initial()
        if operation == "query":
            return self.session.query(
                case_id=body["case_id"],
                version=body["version"],
                question=body["question"],
                request_id=body["request_id"],
            )

        from airlock.report import render_report_markdown, validate_report

        # Agent-written content receives only source-independent checks. Using
        # private source values here would expose a secret-guessing oracle.
        enforce_public_payload_is_safe(body["draft"])
        report = validate_report(body["draft"], self.session.issued_facts)
        response = {
            "schema_version": PROTOCOL,
            "case_id": self.session.case_id,
            "version": self.session.version,
            "status": "REPORT_VALIDATED",
            "report": report,
            "markdown": render_report_markdown(report),
        }
        enforce_public_payload_is_safe(response)
        return response

    def handle_error(self, request: Any, client_address: Any) -> None:
        # No tracebacks or input-dependent diagnostics on the owner's console.
        pass


class _Handler(BaseHTTPRequestHandler):
    server: LoopbackSessionServer
    protocol_version = "HTTP/1.0"

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format: str, *args: Any) -> None:
        # Paths, questions, headers and credentials must not become access logs.
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self._send(code, error_response("INVALID_REQUEST"))

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = stable_json(payload).encode("utf-8")
        if len(data) > MAX_RESPONSE_BYTES:
            status, data = 413, stable_json(error_response("RESPONSE_LIMIT")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def do_POST(self) -> None:
        try:
            if self.path != "/v1/session":
                self._send(404, error_response("INVALID_REQUEST"))
                return
            hosts = self.headers.get_all("Host", [])
            if hosts != [f"127.0.0.1:{self.server.server_port}"] or self.headers.get("Origin"):
                self._send(403, error_response("ACCESS_DENIED"))
                return
            authorizations = self.headers.get_all("Authorization", [])
            expected = "Bearer " + self.server._bearer
            if len(authorizations) != 1 or not hmac.compare_digest(authorizations[0], expected):
                self._send(401, error_response("ACCESS_DENIED"))
                return
            self.server.request_count += 1
            if self.server.request_count > 100:
                self._send(429, error_response("REQUEST_LIMIT"))
                return
            lengths = self.headers.get_all("Content-Length", [])
            if (
                len(lengths) != 1
                or not lengths[0].isdigit()
                or self.headers.get("Transfer-Encoding")
                or self.headers.get("Content-Type") != "application/json"
            ):
                raise ValueError("Invalid request.")
            length = int(lengths[0])
            if not 0 < length <= MAX_REQUEST_BYTES:
                self._send(413, error_response("REQUEST_LIMIT"))
                return
            data = self.rfile.read(length)
            if len(data) != length:
                raise ValueError("Invalid request.")
            response = self.server.dispatch(parse_object(data))
            # Evidence is already source-guarded by _issue. Reports contain
            # Agent-authored text and must not consult the hidden source set.
            enforce_public_payload_is_safe(response)
            self._send(200, response)
        except AirlockError as error:
            self._send(422, error_response(error.code))
        except (ValueError, TypeError, KeyError, UnicodeError):
            self._send(400, error_response("INVALID_REQUEST"))
        except TimeoutError:
            self._send(408, error_response("REQUEST_TIMEOUT"))
        except Exception:
            self._send(500, error_response("SESSION_FAILED"))


def write_connection(path: Path, config: dict[str, Any]) -> None:
    # O_EXCL prevents overwriting/reusing a connection, including a final symlink.
    # Cross-user Windows ACLs are configured separately by the owner.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(stable_json(config) + "\n")


def main(argv: list[str] | None = None) -> int:
    from airlock.cli import _SafeArgumentParser

    parser = _SafeArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--connection", required=True)
    parser.add_argument("--relevance-backend", choices=("openvino", "lexical"), default="openvino")
    parser.add_argument("--model-dir")
    parser.add_argument("--lifetime-seconds", type=int, default=3600)
    connection: Path | None = None
    written_config: bytes | None = None
    try:
        args = parser.parse_args(argv)
        if not 1 <= args.lifetime_seconds <= 3600:
            raise ValueError("Invalid lifetime.")
        from airlock.session import EvidenceSession

        session = EvidenceSession.create(
            Path(args.path),
            args.task,
            relevance_backend=args.relevance_backend,
            model_dir=args.model_dir,
        )
        session.initial()  # Fail closed before advertising readiness.
        with LoopbackSessionServer(session) as server:
            connection = Path(args.connection)
            config = server.connection_config()
            write_connection(connection, config)
            written_config = (stable_json(config) + "\n").encode("utf-8")
            print(stable_json({"schema_version": PROTOCOL, "status": "READY"}), flush=True)
            deadline = monotonic() + args.lifetime_seconds
            while monotonic() < deadline:
                server.handle_request()
        return 0
    except KeyboardInterrupt:
        return 0
    except AirlockError as error:
        print(stable_json(error_response(error.code)), file=sys.stderr)
        return 1
    except Exception:
        print(stable_json(error_response("SESSION_START_FAILED")), file=sys.stderr)
        return 1
    finally:
        if connection is not None and written_config is not None:
            try:
                if not connection.is_symlink():
                    with connection.open("rb") as stream:
                        current = stream.read(len(written_config) + 1)
                    if current == written_config:
                        connection.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
