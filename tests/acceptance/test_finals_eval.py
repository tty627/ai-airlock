"""End-to-end synthetic disclosure checks, without an LLM or a host agent."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from airlock.relevance import OpenVINORankingUnavailable
from airlock.serialization import estimate_tokens, stable_json

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("finals_eval", ROOT / "benchmark/run_finals_eval.py")
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.fixture(scope="module")
def report():
    return runner.run_evaluation(backend="lexical")


def test_synthetic_evaluation_discloses_its_limits_and_keeps_all_categories(report):
    assert report["case_count"] >= 15
    assert report["dataset_provenance"]["blind_holdout"] is False
    assert report["dataset_provenance"]["agent_or_llm_evaluation"] is False
    categories = {item["category"] for item in report["results"]}
    assert {
        "service_outage",
        "cross_file_identity",
        "insufficient_evidence",
        "untrusted_document",
        "blocked_request",
        "irrelevant_material",
        "conflicting_evidence",
    } <= categories
    assert all(item["task_correctness_measured"] is False for item in report["results"])


def test_all_listed_sensitive_values_and_instruction_are_absent_after_transform(report):
    assert report["summary"]["raw_context"]["sensitive_markers_observed_count"] > 0
    assert report["summary"]["raw_context"]["untrusted_markers_observed_count"] > 0
    for variant in ("simple_sanitized", "session_initial", "session_scripted_followups"):
        assert report["summary"][variant]["sensitive_markers_observed_count"] == 0
        assert report["summary"][variant]["untrusted_markers_observed_count"] == 0
    assert report["blocked_request_count"] == report["correct_policy_block_count"] == 2
    assert report["unexpected_policy_block_count"] == 0


def test_followups_release_new_evidence_and_all_wire_responses_are_counted(report):
    case = next(item for item in report["results"] if item["case_id"] == "catalog_revision")
    assert case["new_required_evidence_ids_after_followups"]
    total = case["variants"]["session_scripted_followups"]
    assert total["retained_evidence_count"] == total["required_evidence_count"] == 3
    assert total["duplicate_fact_id_count"] == 0
    expected = sum(estimate_tokens(stable_json(value)) for value in case["session_response_trace"])
    assert total["full_responses_tokens_estimated"] == expected
    # Protocol overhead on small examples must remain visible, not be subtracted.
    assert expected > case["variants"]["raw_context"]["full_responses_tokens_estimated"]


def test_evidence_metric_requires_the_named_source_but_leak_check_covers_metadata():
    case = {
        "required_evidence": [{"id": "e1", "source": "real.txt", "marker": "key fact"}],
        "sensitive_markers": [{"id": "s1", "value": "SYNTHETIC_ONLY_VALUE"}],
        "untrusted_markers": [],
        "identity_pairs": [],
    }
    responses = [
        {
            "task": "key fact SYNTHETIC_ONLY_VALUE",
            "safe_context": {"facts": [{"id": "f1", "source": "wrong.txt", "text": "key fact"}]},
        }
    ]
    measured = runner.measure_responses(case, responses, 0.0)
    assert measured["retained_evidence_count"] == 0
    assert measured["sensitive_markers_observed_count"] == 1


@pytest.mark.parametrize("case_id", ["host_identity", "customer_identity"])
def test_cross_file_identity_remains_linkable_after_disclosure(report, case_id):
    case = next(item for item in report["results"] if item["case_id"] == case_id)
    identity = case["variants"]["session_scripted_followups"]["identity_observations"][0]
    assert identity["all_sources_disclosed"] is True
    assert identity["shared_typed_pseudonym_observed"] is True


def test_requested_openvino_backend_cannot_fall_back_even_for_blocked_only_case(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OpenVINORankingUnavailable()

    monkeypatch.setattr("airlock.relevance.rank_openvino_evidence", unavailable)
    with pytest.raises(OpenVINORankingUnavailable):
        runner.run_evaluation(backend="openvino", case_ids=["blocked_exfil_en"])


def test_unavailable_openvino_cli_returns_failure_without_writing_success(monkeypatch, tmp_path):
    def unavailable(*args, **kwargs):
        raise OpenVINORankingUnavailable()

    monkeypatch.setattr("airlock.relevance.rank_openvino_evidence", unavailable)
    output = tmp_path / "result.json"
    assert runner.main(["--backend", "openvino", "--output", str(output)]) == 2
    assert not output.exists()
