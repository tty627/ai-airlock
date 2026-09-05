"""Validate an Agent-written report without claiming to validate its reasoning.

The caller binds the case and snapshot version and supplies *only* facts already
issued in that case. No model is called here. Successful validation proves
citation membership and the existing output guard's checks, not entailment.
"""

from __future__ import annotations

import re
import string
import unicodedata
from collections.abc import Iterable, Sequence
from typing import Any

from airlock.capsule.leak_guard import enforce_public_payload_is_safe
from airlock.serialization import stable_json

VALIDATION_SCOPE = "citation_membership_and_sensitive_output_only"
SEMANTIC_CORRECTNESS = "not_evaluated"
REFERENCE_SCOPE = "sanitized_snapshot"
MAX_DRAFT_BYTES = 65_536
MAX_REPORT_BYTES = 131_072
MAX_ISSUED_FACTS = 4096
MAX_SECTIONS = 12
MAX_CLAIMS = 100
MAX_CLAIM_CHARS = 2000
MAX_CITATIONS_PER_CLAIM = 12

_DRAFT_KEYS = {"title", "sections", "unresolved_questions"}
_VALIDATED_KEYS = _DRAFT_KEYS | {"validation_scope", "semantic_correctness", "reference_scope"}
_EVIDENCE_KEYS = {"id", "source", "local_ref"}
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,127}\Z")
_LOCAL_REF = re.compile(r"L([1-9][0-9]{0,8})(?:-L([1-9][0-9]{0,8}))?\Z")
_URL = re.compile(
    r"(?:[a-z][a-z0-9+.-]{1,31}:[/\\]|"
    r"(?:javascript|vbscript|data|mailto):|www\.)",
    re.IGNORECASE,
)
_MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\s*(?:\(|\[|:)")
_MARKDOWN_ESCAPE = re.compile("([" + re.escape(string.punctuation) + "])")


class ReportValidationError(ValueError):
    """Input-independent error suitable for an externally visible boundary."""

    code = "REPORT_VALIDATION_FAILED"
    public_message = "The report failed validation; no report was released."

    def __init__(self) -> None:
        super().__init__(self.public_message)


def _require_keys(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ReportValidationError()
    return value


def _text(value: Any, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ReportValidationError()
    # Every field is one plain-text line. Reject invisible controls, directional
    # overrides and malformed Unicode instead of hiding them during rendering.
    if any(
        unicodedata.category(character).startswith("C")
        or unicodedata.category(character) in {"Zl", "Zp"}
        for character in value
    ):
        raise ReportValidationError()
    normalized = unicodedata.normalize("NFKC", value)
    if (
        "<" in normalized
        or ">" in normalized
        or _URL.search(normalized)
        or _MARKDOWN_LINK.search(normalized)
    ):
        raise ReportValidationError()
    return value


def _bounded_list(value: Any, maximum: int, *, allow_empty: bool = True) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum or (not allow_empty and not value):
        raise ReportValidationError()
    return value


def _check_size(value: dict[str, Any], maximum: int) -> None:
    if len(stable_json(value).encode("utf-8")) > maximum:
        raise ReportValidationError()


def _evidence_metadata(fact: Any) -> dict[str, str]:
    if not isinstance(fact, dict) or not _EVIDENCE_KEYS.issubset(fact):
        raise ReportValidationError()
    identity = fact["id"]
    if not isinstance(identity, str) or not _ID.fullmatch(identity):
        raise ReportValidationError()
    source = _text(fact["source"], 512)
    # A source is a display-only relative snapshot path, never a URL or an
    # absolute/parent path. Line references refer to the sanitized snapshot.
    path = source.replace("\\", "/")
    if (
        path.startswith("/")
        or ":" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
    ):
        raise ReportValidationError()
    local_ref = fact["local_ref"]
    match = _LOCAL_REF.fullmatch(local_ref) if isinstance(local_ref, str) else None
    if match is None or (match[2] is not None and int(match[1]) > int(match[2])):
        raise ReportValidationError()
    return {"id": identity, "source": source, "local_ref": local_ref}


def validate_report(
    draft: dict[str, Any],
    issued_facts: Sequence[dict[str, Any]],
    *,
    sensitive_values: Iterable[str] = (),
) -> dict[str, Any]:
    """Validate plain-text claims against the caller's current-case issued facts.

    ``draft`` contains exactly ``title``, ``sections`` and
    ``unresolved_questions``. Sections have ``heading`` and ``claims``; each
    claim has ``text`` and one or more ``evidence_ids``. Unknown keys, unknown
    IDs and duplicate citations within a claim fail closed. Reusing a fact in
    separate claims is allowed. An unanswered task may have no sections and
    one or more unresolved questions.

    All generated text and returned source metadata pass the existing public
    payload guard. The function preserves text, does not invent a diagnosis,
    and deliberately does not score whether evidence supports an assertion.
    """

    _require_keys(draft, _DRAFT_KEYS)
    if (
        not isinstance(issued_facts, Sequence)
        or isinstance(issued_facts, (str, bytes))
        or len(issued_facts) > MAX_ISSUED_FACTS
    ):
        raise ReportValidationError()
    facts_by_id: dict[str, dict[str, str]] = {}
    for fact in issued_facts:
        metadata = _evidence_metadata(fact)
        if metadata["id"] in facts_by_id:
            raise ReportValidationError()
        facts_by_id[metadata["id"]] = metadata

    title = _text(draft["title"], 160)
    sections: list[dict[str, Any]] = []
    count = 0
    for section in _bounded_list(draft["sections"], MAX_SECTIONS):
        _require_keys(section, {"heading", "claims"})
        heading = _text(section["heading"], 120)
        claims: list[dict[str, Any]] = []
        for claim in _bounded_list(section["claims"], MAX_CLAIMS, allow_empty=False):
            _require_keys(claim, {"text", "evidence_ids"})
            count += 1
            if count > MAX_CLAIMS:
                raise ReportValidationError()
            claim_text = _text(claim["text"], MAX_CLAIM_CHARS)
            evidence_ids = _bounded_list(
                claim["evidence_ids"], MAX_CITATIONS_PER_CLAIM, allow_empty=False
            )
            if any(not isinstance(identity, str) for identity in evidence_ids):
                raise ReportValidationError()
            if len(set(evidence_ids)) != len(evidence_ids) or any(
                identity not in facts_by_id for identity in evidence_ids
            ):
                raise ReportValidationError()
            claims.append(
                {
                    "text": claim_text,
                    "evidence_ids": list(evidence_ids),
                    "evidence": [dict(facts_by_id[identity]) for identity in evidence_ids],
                }
            )
        sections.append({"heading": heading, "claims": claims})
    questions = [
        _text(question, 1000) for question in _bounded_list(draft["unresolved_questions"], 20)
    ]
    if not sections and not questions:
        raise ReportValidationError()

    # Only bounded, type-checked fields reach serialization or output scanning.
    _check_size(draft, MAX_DRAFT_BYTES)
    result = {
        "title": title,
        "sections": sections,
        "unresolved_questions": questions,
        "validation_scope": VALIDATION_SCOPE,
        "semantic_correctness": SEMANTIC_CORRECTNESS,
        "reference_scope": REFERENCE_SCOPE,
    }
    _check_size(result, MAX_REPORT_BYTES)
    enforce_public_payload_is_safe(result, sensitive_values)
    return result


def _checked_render_input(validated: dict[str, Any]) -> dict[str, Any]:
    """Check render structure again; callers remain responsible for provenance."""

    _require_keys(validated, _VALIDATED_KEYS)
    if (
        validated["validation_scope"] != VALIDATION_SCOPE
        or validated["semantic_correctness"] != SEMANTIC_CORRECTNESS
        or validated["reference_scope"] != REFERENCE_SCOPE
    ):
        raise ReportValidationError()
    sections: list[dict[str, Any]] = []
    facts: dict[str, dict[str, str]] = {}
    for section in _bounded_list(validated["sections"], MAX_SECTIONS):
        _require_keys(section, {"heading", "claims"})
        claims = []
        for claim in _bounded_list(section["claims"], MAX_CLAIMS, allow_empty=False):
            _require_keys(claim, {"text", "evidence_ids", "evidence"})
            evidence = _bounded_list(claim["evidence"], MAX_CITATIONS_PER_CLAIM)
            evidence_ids = _bounded_list(claim["evidence_ids"], MAX_CITATIONS_PER_CLAIM)
            if len(evidence) != len(evidence_ids):
                raise ReportValidationError()
            for identity, item in zip(evidence_ids, evidence, strict=True):
                _require_keys(item, _EVIDENCE_KEYS)
                metadata = _evidence_metadata(item)
                if identity != metadata["id"] or (
                    metadata["id"] in facts and facts[metadata["id"]] != metadata
                ):
                    raise ReportValidationError()
                facts[metadata["id"]] = metadata
            claims.append({"text": claim["text"], "evidence_ids": list(evidence_ids)})
        sections.append({"heading": section["heading"], "claims": claims})
    return validate_report(
        {
            "title": validated["title"],
            "sections": sections,
            "unresolved_questions": validated["unresolved_questions"],
        },
        list(facts.values()),
    )


def _escape(text: str) -> str:
    # CommonMark permits escaping every ASCII punctuation character. Escaping
    # ampersands also prevents user-written entities from turning into markup.
    return _MARKDOWN_ESCAPE.sub(r"\\\1", text)


def render_report_markdown(validated: dict[str, Any]) -> str:
    """Render ``validate_report`` output with no active links or raw markup.

    Rechecking here protects the rendering boundary, but cannot prove that a
    dictionary supplied by an untrusted caller came from ``validate_report``.
    The case owner must validate the draft against its issued facts first.
    """

    report = _checked_render_input(validated)
    lines = [
        "# " + _escape(report["title"]),
        "",
        "Validation scope: citation membership and sensitive output checks only.",
        "Semantic correctness: not evaluated.",
        "Source line references: sanitized snapshot, not original-file line numbers.",
        "",
    ]
    for section in report["sections"]:
        lines.extend(["## " + _escape(section["heading"]), ""])
        for claim in section["claims"]:
            lines.append("- " + _escape(claim["text"]))
            for evidence in claim["evidence"]:
                citation = f"{evidence['id']}: {evidence['source']} ({evidence['local_ref']})"
                lines.append("  - Evidence: " + _escape(citation))
        lines.append("")
    if report["unresolved_questions"]:
        lines.extend(["## Unresolved questions", ""])
        lines.extend("- " + _escape(question) for question in report["unresolved_questions"])
        lines.append("")
    rendered = "\n".join(lines)
    if len(rendered.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ReportValidationError()
    enforce_public_payload_is_safe(rendered)
    return rendered
