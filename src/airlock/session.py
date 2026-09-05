"""In-memory, bounded disclosure from a single sanitized input snapshot.

This module is a disclosure protocol, not an operating-system sandbox.  Only
``create`` may ingest source files.  Follow-ups work on the complete sanitized
snapshot, with already-issued lines masked without renumbering.  References
address that snapshot: upstream multiline redaction can change raw-file lines.

The budget covers canonical JSON of each newly issued successful response,
including metadata.  It is a UTF-8 byte estimate, not model tokenizer usage or
an end-to-end Agent cost.  Cached retries do not represent new disclosure.
"""

from __future__ import annotations

import hashlib
import re
import threading
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from airlock.capsule.leak_guard import enforce_public_payload_is_safe, inspect_public_payload
from airlock.capsule.pseudonymizer import ConsistentPseudonymizer
from airlock.capsule.redactor import SensitiveValues, transform_text
from airlock.detectors import Sensitivity, detect_all
from airlock.errors import (
    AirlockError,
    ConfigurationError,
    InferenceUnavailableError,
    InputIncompleteError,
    NoSafeContextError,
    UnsafeTaskError,
)
from airlock.pipeline import _policy, _prepare_workspace, _task_requests_exfiltration
from airlock.relevance import (
    OpenVINORankingUnavailable,
    RankingError,
    openvino_inference_metadata,
    rank_evidence,
    rank_openvino_evidence,
)
from airlock.relevance.ranker import TOKEN_ESTIMATOR, RankedFact
from airlock.serialization import estimate_tokens, stable_json

_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_RANKED_CANDIDATE_LIMIT = 64
_HEX_ALPHABET = str.maketrans("0123456789abcdef", "abcdefghijklmnop")
_ERRORS = {
    "CASE_MISMATCH": "The request does not address this evidence snapshot.",
    "INVALID_REQUEST": "The evidence request is invalid.",
    "REQUEST_ID_CONFLICT": "The request identifier has already been used.",
    "FOLLOWUP_LIMIT_REACHED": "The session follow-up limit has been reached.",
    "TOKEN_BUDGET_EXHAUSTED": "The session disclosure budget has been reached.",
}


class SessionError(AirlockError):
    """Only fixed, input-independent errors may leave the session boundary."""

    def __init__(self, code: str) -> None:
        self.code = code if code in _ERRORS else "INVALID_REQUEST"
        self.public_message = _ERRORS[self.code]
        super().__init__()


@dataclass(frozen=True, slots=True)
class SessionLimits:
    max_followups: int = 2
    max_facts_per_round: int = 3
    max_total_tokens: int = 6000
    max_question_chars: int = 2000

    def __post_init__(self) -> None:
        bounds = (
            (self.max_followups, 0, 2),
            (self.max_facts_per_round, 1, 8),
            (self.max_total_tokens, 512, 100_000),
            (self.max_question_chars, 1, 10_000),
        )
        if any(
            type(value) is not int or not lower <= value <= upper for value, lower, upper in bounds
        ):
            raise ConfigurationError()


def _unsafe_request(text: str) -> bool:
    return (
        _task_requests_exfiltration(text)
        or any(
            f.sensitivity is Sensitivity.UNTRUSTED_INSTRUCTION
            for f in detect_all(text, "<request>")
        )
        or inspect_public_payload({"request": text}).untrusted_instruction_spans_forwarded > 0
    )


class EvidenceSession:
    """Thread-safe session.  Construct through :meth:`create`, never serialize it."""

    def __init__(self) -> None:
        raise ConfigurationError()

    @classmethod
    def create(
        cls,
        path: str | Path,
        task: str,
        *,
        relevance_backend: str = "openvino",
        model_dir: str | Path | None = None,
        limits: SessionLimits = SessionLimits(),
    ) -> EvidenceSession:
        if (
            not isinstance(limits, SessionLimits)
            or not isinstance(task, str)
            or not task.strip()
            or len(task) > limits.max_question_chars
            or relevance_backend not in {"lexical", "openvino"}
        ):
            raise ConfigurationError()
        # Reject unsafe tasks before opening any input files.
        if _unsafe_request(task):
            raise UnsafeTaskError()
        policy = _policy(None)
        pseudonymizer = ConsistentPseudonymizer()
        transformed_task = transform_text(task, detect_all(task, "<task>"), pseudonymizer)
        workspace = _prepare_workspace(path, policy, pseudonymizer)
        protected = SensitiveValues(
            (*workspace.sensitive_values, *transformed_task.sensitive_values)
        )
        documents = dict(workspace.transformed_documents)
        enforce_public_payload_is_safe(
            {"task": transformed_task.text, "documents": list(documents.items())}, protected
        )
        if not any(
            line.strip() and line.strip() != "[UNTRUSTED_INSTRUCTION_ISOLATED]"
            for text in documents.values()
            for line in text.splitlines()
        ):
            raise NoSafeContextError()

        session = object.__new__(cls)
        # Preserve all identifier entropy without random digit runs that can
        # resemble phone numbers to the independent output detector.
        session._case_id = "case_" + uuid4().hex.translate(_HEX_ALPHABET)
        # Including a fresh case identity prevents cross-session reference reuse.
        session._version = "snapshot_" + hashlib.sha256(
            (session._case_id + stable_json(documents)).encode("utf-8")
        ).hexdigest()[:24].translate(_HEX_ALPHABET)
        session._task = transformed_task.text
        session._documents = MappingProxyType(documents)
        session._sensitive_values = protected
        session._limits = limits
        session._backend = relevance_backend
        session._model_dir = model_dir
        session._lock = threading.RLock()
        session._issued: dict[str, dict[str, Any]] = {}
        session._released_lines: dict[str, set[int]] = {}
        session._cache: dict[str, tuple[str, dict[str, Any]]] = {}
        session._initial: dict[str, Any] | None = None
        session._used_tokens = 0
        session._followups = 0
        # Do not retain ingestion, findings, original task or PII identity map.
        # Only opaque in-memory leak-gate material survives preparation.
        del workspace, pseudonymizer, transformed_task
        return session

    @property
    def case_id(self) -> str:
        return self._case_id

    @property
    def version(self) -> str:
        return self._version

    @property
    def task(self) -> str:
        return self._task

    @property
    def limits(self) -> SessionLimits:
        return self._limits

    @property
    def relevance_backend(self) -> str:
        return self._backend

    @property
    def issued_facts(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(deepcopy(fact) for fact in self._issued.values())

    def check_public_payload(self, payload: Any) -> None:
        """Guard source-derived evidence; never use on Agent-authored input."""
        with self._lock:
            enforce_public_payload_is_safe(payload, self._sensitive_values)

    def initial(self) -> dict[str, Any]:
        """Issue once; retries return the exact original accounting snapshot."""
        with self._lock:
            if self._initial is None:
                self._initial = self._issue(self._task, round_number=0)
            return deepcopy(self._initial)

    def query(
        self,
        case_id: str,
        version: str,
        question: str,
        request_id: str,
    ) -> dict[str, Any]:
        """Release new evidence only, with fixed scope and idempotent request IDs."""
        with self._lock:
            if case_id != self._case_id or version != self._version:
                raise SessionError("CASE_MISMATCH")
            if (
                not isinstance(question, str)
                or not question.strip()
                or len(question) > self._limits.max_question_chars
                or not isinstance(request_id, str)
                or not _REQUEST_ID.fullmatch(request_id)
            ):
                raise SessionError("INVALID_REQUEST")
            fingerprint = hashlib.sha256(question.encode("utf-8")).hexdigest()
            if request_id in self._cache:
                previous, payload = self._cache[request_id]
                if fingerprint != previous:
                    raise SessionError("REQUEST_ID_CONFLICT")
                return deepcopy(payload)

            if _unsafe_request(question):
                raise UnsafeTaskError()
            if self._followups >= self._limits.max_followups:
                raise SessionError("FOLLOWUP_LIMIT_REACHED")

            # Query PII is redacted, not assigned fresh misleading identities.
            # Callers can use snapshot pseudonyms from earlier evidence.
            safe = transform_text(
                question,
                detect_all(question, "<query>"),
                pii_mode="redact",
                internal_ip_mode="redact",
            )
            # Agent-written input must not be compared with private source
            # values: accept/reject would become a secret-guessing oracle.
            # It is never echoed, and cannot mutate the fixed snapshot guard.
            enforce_public_payload_is_safe({"question": safe.text})
            self.initial()
            result = self._issue(safe.text, round_number=self._followups + 1)
            self._followups += 1
            self._cache[request_id] = (fingerprint, result)
            return deepcopy(result)

    def _remaining_documents(self) -> dict[str, str]:
        # Blank released lines; removing them would corrupt stable references.
        return {
            source: "\n".join(
                "" if number in self._released_lines.get(source, ()) else line
                for number, line in enumerate(text.splitlines(), 1)
            )
            for source, text in self._documents.items()
        }

    def _rank(self, question: str, documents: dict[str, str]) -> tuple[Any, dict[str, Any]]:
        remaining = self._limits.max_total_tokens - self._used_tokens
        if remaining <= 0:
            raise SessionError("TOKEN_BUDGET_EXHAUSTED")
        kwargs = {
            # Retrieve a bounded pool before fitting the full response envelope.
            # A large top candidate must not hide a smaller candidate that fits.
            "max_facts": _RANKED_CANDIDATE_LIMIT,
            "max_tokens": _RANKED_CANDIDATE_LIMIT * self._limits.max_total_tokens,
            "reserved_tokens": 0,
        }
        try:
            if self._backend == "openvino":
                ranked = rank_openvino_evidence(
                    question, documents, model_dir=self._model_dir, **kwargs
                )
                inference = (
                    openvino_inference_metadata(chunks_processed=ranked.candidate_windows)
                    if ranked.candidate_windows
                    else {
                        "mode": "not_run",
                        "requested_backend": "openvino",
                        "reason": "NO_NEW_EVIDENCE",
                        "fallback_state": "not_used",
                    }
                )
            else:
                ranked = rank_evidence(question, documents, **kwargs)
                inference = {
                    "mode": "deterministic_lexical_v1",
                    "openvino_available": False,
                    "fallback_state": "not_used",
                }
        except OpenVINORankingUnavailable:
            raise InferenceUnavailableError() from None
        except RankingError:
            raise InputIncompleteError() from None
        return ranked, inference

    def _new_facts(
        self,
        ranked: RankedFact,
        released: dict[str, set[int]],
    ) -> list[dict[str, Any]]:
        lines = self._documents[ranked.source].splitlines()
        already = released.get(ranked.source, set())
        ranges: list[tuple[int, int]] = []
        start: int | None = None
        for number in range(ranked.start_line, ranked.end_line + 2):
            if number <= ranked.end_line and number not in already:
                if start is None:
                    start = number
            elif start is not None:
                ranges.append((start, number - 1))
                start = None
        facts = []
        for start, end in ranges:
            while start <= end and not lines[start - 1].strip():
                start += 1
            while end >= start and not lines[end - 1].strip():
                end -= 1
            if start > end:
                continue
            text = "\n".join(lines[start - 1 : end])
            if not any(
                line.strip() and line.strip() != "[UNTRUSTED_INSTRUCTION_ISOLATED]"
                for line in text.splitlines()
            ):
                continue
            local_ref = f"L{start}" if start == end else f"L{start}-L{end}"
            identity = stable_json([self._case_id, self._version, ranked.source, local_ref, text])
            facts.append(
                {
                    "id": "evidence_"
                    + hashlib.sha256(identity.encode()).hexdigest()[:24].translate(_HEX_ALPHABET),
                    "text": text,
                    "source": ranked.source,
                    "local_ref": local_ref,
                    "start_line": start,
                    "end_line": end,
                }
            )
        return facts

    def _response(
        self,
        facts: list[dict[str, Any]],
        *,
        round_number: int,
        inference: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        result = {
            "schema_version": "finals-session-v1",
            "case_id": self._case_id,
            "version": self._version,
            "round": round_number,
            "status": status,
            "task": self._task,
            "safe_context": {"facts": facts, "reference_scope": "sanitized_snapshot"},
            "budget": {
                "token_estimator": TOKEN_ESTIMATOR,
                "accounting_scope": "canonical_json_new_responses_retries_excluded",
                "round_tokens_estimated": 0,
                "cumulative_tokens_estimated": self._used_tokens,
                "max_total_tokens": self._limits.max_total_tokens,
                "max_followups": self._limits.max_followups,
                "rounds_used": round_number,
            },
            "inference": inference,
        }
        # Account for the digits of the accounting fields themselves.
        while True:
            cost = estimate_tokens(result)
            if cost == result["budget"]["round_tokens_estimated"]:
                break
            result["budget"]["round_tokens_estimated"] = cost
            result["budget"]["cumulative_tokens_estimated"] = self._used_tokens + cost
        return result

    def _issue(self, question: str, *, round_number: int) -> dict[str, Any]:
        ranked, inference = self._rank(question, self._remaining_documents())
        selected: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        released = {source: set(lines) for source, lines in self._released_lines.items()}
        for candidate in ranked.facts:
            for fact in self._new_facts(candidate, released):
                if len(selected) >= self._limits.max_facts_per_round:
                    break
                if fact["id"] in selected_ids:
                    continue
                proposed = self._response(
                    [*selected, fact], round_number=round_number, inference=inference, status="OK"
                )
                if (
                    proposed["budget"]["cumulative_tokens_estimated"]
                    <= self._limits.max_total_tokens
                ):
                    selected.append(fact)
                    selected_ids.add(fact["id"])
                    released.setdefault(fact["source"], set()).update(
                        range(fact["start_line"], fact["end_line"] + 1)
                    )
        status = "OK" if selected else "NO_NEW_EVIDENCE"
        if not selected and (ranked.facts or ranked.status == "TOKEN_BUDGET_EXHAUSTED"):
            raise SessionError("TOKEN_BUDGET_EXHAUSTED")
        result = self._response(
            selected, round_number=round_number, inference=inference, status=status
        )
        if result["budget"]["cumulative_tokens_estimated"] > self._limits.max_total_tokens:
            raise SessionError("TOKEN_BUDGET_EXHAUSTED")
        # No session accounting or evidence is committed before this final gate.
        self.check_public_payload(result)
        for fact in selected:
            self._issued[fact["id"]] = deepcopy(fact)
            self._released_lines.setdefault(fact["source"], set()).update(
                range(fact["start_line"], fact["end_line"] + 1)
            )
        self._used_tokens = result["budget"]["cumulative_tokens_estimated"]
        return result
