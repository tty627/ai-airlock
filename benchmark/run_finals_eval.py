"""Reproducible synthetic evidence-disclosure checks; no LLM is called.

Run from a checkout: python benchmark/run_finals_eval.py --backend lexical
The follow-up questions are public, scripted presets, not agent decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from time import perf_counter_ns
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from airlock.capsule.pseudonymizer import ConsistentPseudonymizer  # noqa: E402
from airlock.capsule.redactor import transform_text  # noqa: E402
from airlock.detectors import detect_all  # noqa: E402
from airlock.errors import AirlockError  # noqa: E402
from airlock.relevance import OpenVINORankingUnavailable  # noqa: E402
from airlock.serialization import estimate_tokens, stable_json  # noqa: E402
from airlock.session import EvidenceSession, SessionLimits  # noqa: E402

DEFAULT_CASES = REPO_ROOT / "benchmark" / "finals_cases.json"
VARIANTS = ("raw_context", "simple_sanitized", "session_initial", "session_scripted_followups")


def load_cases(path: Path = DEFAULT_CASES) -> tuple[dict[str, Any], str]:
    """Validate public fixtures before creating any temporary input files."""
    data = path.read_bytes()
    dataset = json.loads(data)
    if dataset.get("schema_version") != "finals-cases-v1":
        raise ValueError("UNSUPPORTED_CASE_SCHEMA")
    seen: set[str] = set()
    for case in dataset["cases"]:
        if case["id"] in seen or not re.fullmatch(r"[a-z][a-z0-9_]+", case["id"]):
            raise ValueError("INVALID_CASE_ID")
        seen.add(case["id"])
        for source, content in case["documents"].items():
            candidate = PurePosixPath(source)
            if (
                candidate.is_absolute()
                or ".." in candidate.parts
                or "\\" in source
                or not candidate.parts
                or not isinstance(content, str)
            ):
                raise ValueError("INVALID_FIXTURE_PATH")
        for item in case["required_evidence"]:
            if item["marker"] not in case["documents"].get(item["source"], ""):
                raise ValueError("EVIDENCE_MARKER_NOT_IN_SOURCE")
        raw = "\n".join(case["documents"].values())
        for item in case["sensitive_markers"] + case["untrusted_markers"]:
            if not item["value"] or item["value"] not in raw:
                raise ValueError("OBSERVATION_MARKER_NOT_IN_SOURCE")
    return dataset, hashlib.sha256(data).hexdigest()


def _milliseconds(started: int) -> float:
    return round((perf_counter_ns() - started) / 1_000_000, 3)


def _document_payload(documents: dict[str, str]) -> dict[str, Any]:
    return {"documents": [{"source": source, "text": text} for source, text in documents.items()]}


def _simple_sanitize(documents: dict[str, str]) -> dict[str, str]:
    # This baseline shares Airlock detectors, isolates detected instructions,
    # and redacts all PII. It does no retrieval and no task-policy enforcement.
    engine = ConsistentPseudonymizer()
    return {
        source: transform_text(
            text,
            detect_all(text, source),
            engine,
            pii_mode="redact",
            internal_ip_mode="redact",
        ).text
        for source, text in documents.items()
    }


def _evidence_by_source(responses: list[dict[str, Any]]) -> dict[str, str]:
    sources: dict[str, list[str]] = {}
    for response in responses:
        items = response.get("documents", response.get("safe_context", {}).get("facts", []))
        for item in items:
            sources.setdefault(item["source"], []).append(item["text"])
    return {source: "\n".join(parts) for source, parts in sources.items()}


def measure_responses(
    case: dict[str, Any], responses: list[dict[str, Any]], elapsed_ms: float
) -> dict[str, Any]:
    """Measure complete serialized responses, including repeated metadata."""
    serialized = [stable_json(response) for response in responses]
    transmitted = "\n".join(serialized)
    sources = _evidence_by_source(responses)
    retained = [
        item["id"]
        for item in case["required_evidence"]
        if item["marker"] in sources.get(item["source"], "")
    ]
    required = len(case["required_evidence"])
    exposed_sensitive = [
        item["id"] for item in case["sensitive_markers"] if item["value"] in transmitted
    ]
    exposed_untrusted = [
        item["id"] for item in case["untrusted_markers"] if item["value"] in transmitted
    ]
    fact_ids = [
        fact["id"]
        for response in responses
        for fact in response.get("safe_context", {}).get("facts", [])
    ]
    identities = []
    for item in case.get("identity_pairs", []):
        observed = [
            set(re.findall(r"\[" + re.escape(item["kind"]) + r"_\d{3}\]", sources.get(s, "")))
            for s in item["sources"]
        ]
        identities.append(
            {
                "kind": item["kind"],
                "sources": item["sources"],
                "all_sources_disclosed": all(s in sources for s in item["sources"]),
                "shared_typed_pseudonym_observed": bool(observed and set.intersection(*observed)),
            }
        )
    return {
        "required_evidence_count": required,
        "retained_evidence_count": len(retained),
        "retained_evidence_ids": retained,
        "evidence_retention_fraction": len(retained) / required if required else None,
        "sensitive_marker_count": len(case["sensitive_markers"]),
        "sensitive_markers_observed_count": len(exposed_sensitive),
        "sensitive_marker_ids_observed": exposed_sensitive,
        "untrusted_markers_observed_count": len(exposed_untrusted),
        "untrusted_marker_ids_observed": exposed_untrusted,
        "full_response_count": len(responses),
        "full_responses_tokens_estimated": sum(estimate_tokens(value) for value in serialized),
        "full_responses_utf8_bytes": sum(len(value.encode("utf-8")) for value in serialized),
        "elapsed_ms": elapsed_ms,
        "fact_ids": fact_ids,
        "duplicate_fact_id_count": len(fact_ids) - len(set(fact_ids)),
        "identity_observations": identities,
    }


def _strict_backend_preflight(backend: str, model_dir: str | None) -> None:
    if backend not in {"lexical", "openvino"}:
        raise ValueError("INVALID_BACKEND")
    if backend == "openvino":
        from airlock.relevance import rank_openvino_evidence

        # Even a blocked-only selection must fail if the requested backend is
        # unavailable. This never silently measures the lexical implementation.
        rank_openvino_evidence(
            "availability probe",
            {"probe.txt": "availability probe"},
            model_dir=model_dir,
            max_facts=1,
            max_tokens=1000,
            reserved_tokens=0,
        )


def evaluate_case(
    case: dict[str, Any], *, backend: str, model_dir: str | None, limits: SessionLimits
) -> dict[str, Any]:
    variants: dict[str, Any] = {}
    started = perf_counter_ns()
    raw = _document_payload(case["documents"])
    variants["raw_context"] = measure_responses(case, [raw], _milliseconds(started))
    started = perf_counter_ns()
    sanitized = _document_payload(_simple_sanitize(case["documents"]))
    variants["simple_sanitized"] = measure_responses(case, [sanitized], _milliseconds(started))
    responses: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="airlock-finals-") as directory:
        root = Path(directory)
        for source, text in case["documents"].items():
            target = root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        started = perf_counter_ns()
        try:
            session = EvidenceSession.create(
                path=root,
                task=case["task"],
                relevance_backend=backend,
                model_dir=model_dir,
                limits=limits,
            )
            initial = session.initial()
        except AirlockError as error:
            if error.code not in {"TASK_BLOCKED", "NO_SAFE_CONTEXT"}:
                raise
            session = None
            initial = {"status": "error", "error": {"code": error.code}}
        responses.append(initial)
        initial_elapsed = _milliseconds(started)
        variants["session_initial"] = measure_responses(case, responses, initial_elapsed)
        for number, question in enumerate(case["scripted_preset_questions"], start=1):
            if session is None:
                break
            try:
                response = session.query(
                    case_id=session.case_id,
                    version=session.version,
                    question=question,
                    request_id=f"preset-{number}",
                )
            except AirlockError as error:
                if error.code == "INFERENCE_UNAVAILABLE":
                    raise
                responses.append({"status": "error", "error": {"code": error.code}})
                events.append({"preset_question_index": number, "error_code": error.code})
                break
            responses.append(response)
            events.append(
                {
                    "preset_question_index": number,
                    "status": response.get("status"),
                    "new_fact_count": len(response.get("safe_context", {}).get("facts", [])),
                }
            )
        cumulative_elapsed = _milliseconds(started)
        variants["session_scripted_followups"] = measure_responses(
            case, responses, cumulative_elapsed
        )
    initial_ids = set(variants["session_initial"]["retained_evidence_ids"])
    total_ids = set(variants["session_scripted_followups"]["retained_evidence_ids"])
    block_observed = (
        initial.get("decision") == "BLOCK"
        or initial.get("status") == "TASK_BLOCKED"
        or initial.get("error", {}).get("code") == "TASK_BLOCKED"
    )
    return {
        "case_id": case["id"],
        "category": case["category"],
        "expected_answerable_label_only": case["expected_answerable"],
        "expected_blocked": case["expected_blocked"],
        "task_policy_block_observed": block_observed,
        "task_correctness_measured": False,
        "scripted_preset_questions": case["scripted_preset_questions"],
        "followup_events": events,
        "new_required_evidence_ids_after_followups": sorted(total_ids - initial_ids),
        "variants": variants,
        "session_response_trace": responses,
    }


def run_evaluation(
    *,
    cases_path: Path = DEFAULT_CASES,
    backend: str = "lexical",
    model_dir: str | None = None,
    case_ids: list[str] | None = None,
    limits: SessionLimits | None = None,
) -> dict[str, Any]:
    dataset, digest = load_cases(cases_path)
    selected = dataset["cases"]
    if case_ids:
        wanted = set(case_ids)
        available = {case["id"] for case in selected}
        if wanted - available:
            raise ValueError("UNKNOWN_CASE_ID")
        selected = [case for case in selected if case["id"] in wanted]
    _strict_backend_preflight(backend, model_dir)
    active_limits = limits if limits is not None else SessionLimits()
    results = [
        evaluate_case(case, backend=backend, model_dir=model_dir, limits=active_limits)
        for case in selected
    ]
    summary: dict[str, Any] = {}
    for variant in VARIANTS:
        measures = [result["variants"][variant] for result in results]
        required = sum(item["required_evidence_count"] for item in measures)
        retained = sum(item["retained_evidence_count"] for item in measures)
        summary[variant] = {
            "required_evidence_count": required,
            "retained_evidence_count": retained,
            "evidence_retention_fraction": retained / required if required else None,
            "sensitive_markers_observed_count": sum(
                item["sensitive_markers_observed_count"] for item in measures
            ),
            "untrusted_markers_observed_count": sum(
                item["untrusted_markers_observed_count"] for item in measures
            ),
            "full_responses_tokens_estimated": sum(
                item["full_responses_tokens_estimated"] for item in measures
            ),
            "elapsed_ms": round(sum(item["elapsed_ms"] for item in measures), 3),
        }
    return {
        "schema_version": "finals-eval-v1",
        "dataset_sha256": digest,
        "dataset_provenance": dataset["provenance"],
        "backend_requested": backend,
        "case_count": len(results),
        "measurement_contract": {
            "token_estimator": "utf8_bytes_div_4_ceil_v1",
            "token_scope": "sum of every complete response JSON; metadata included",
            "error_transport": "Python exceptions become this runner's static JSON error envelope",
            "not_measured": [
                "LLM root-cause correctness or final task completion",
                "autonomous selection of follow-up questions",
                "provider-billed prompt/output tokens or host conversation overhead",
                "Core Ultra hardware compliance, OS isolation, or human usability",
            ],
            "baseline": "shared detectors, full sanitized context, all PII redacted; no task block",
            "timing_scope": (
                "context construction and local retrieval only; session includes preparation; "
                "excludes fixture I/O, OpenVINO preflight, host and LLM latency"
            ),
            "comparability_warning": (
                "Full response protocol overhead can exceed raw context on these short fixtures. "
                "No token saving or task quality improvement is assumed."
            ),
        },
        "summary": summary,
        "blocked_request_count": sum(result["expected_blocked"] for result in results),
        "correct_policy_block_count": sum(
            result["expected_blocked"] and result["task_policy_block_observed"]
            for result in results
        ),
        "unexpected_policy_block_count": sum(
            not result["expected_blocked"] and result["task_policy_block_observed"]
            for result in results
        ),
        "cases_with_new_required_evidence": sum(
            bool(result["new_required_evidence_ids_after_followups"]) for result in results
        ),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("lexical", "openvino"), default="lexical")
    parser.add_argument("--model-dir")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_evaluation(
            cases_path=args.cases,
            backend=args.backend,
            model_dir=args.model_dir,
            case_ids=args.case_ids,
        )
    except (AirlockError, OpenVINORankingUnavailable) as error:
        code = error.code if isinstance(error, AirlockError) else "INFERENCE_UNAVAILABLE"
        print(stable_json({"status": "error", "error": {"code": code}}), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(stable_json({"output": str(args.output), "summary": report["summary"]}))
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
