from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from airlock.relevance.openvino_ranker import (
    DEFAULT_MODEL_SUBDIR,
    MANIFEST_FILENAME,
    MAX_CHUNK_UTF8_BYTES,
    MODEL_DIR_ENV,
    MODEL_FORMAT,
    MODEL_ID,
    MODEL_REVISION,
    OpenVINORankingUnavailable,
    _candidate_scope_anchor,
    _candidate_windows,
    _line_scope_anchor,
    _scope_calibration,
    _token_safe_fragments,
    _utf8_fragments,
    rank_openvino_evidence,
    resolve_model_dir,
    validate_model_dir,
)
from airlock.serialization import stable_json


class _FakeBackend:
    def __init__(self, relevant_marker: str | None) -> None:
        self.relevant_marker = relevant_marker
        self.query_inputs: list[str] = []
        self.document_inputs: list[str] = []

    def embed_query(self, text: str) -> list[float]:
        self.query_inputs.append(text)
        return [1.0, 0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_inputs.extend(texts)
        return [
            [1.0, 0.0]
            if self.relevant_marker is not None and self.relevant_marker in text
            else [0.0, 1.0]
            for text in texts
        ]


class _SimilarityBackend:
    def __init__(self, similarity: float) -> None:
        self.similarity = similarity

    def embed_query(self, text: str) -> list[float]:  # noqa: ARG002
        return [1.0, 0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        perpendicular = math.sqrt(1.0 - self.similarity**2)
        return [[self.similarity, perpendicular] for _text in texts]


def test_default_and_relative_model_paths_do_not_depend_on_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    expected = (repository_root / DEFAULT_MODEL_SUBDIR).resolve()
    monkeypatch.delenv(MODEL_DIR_ENV, raising=False)
    monkeypatch.chdir(tmp_path)

    assert resolve_model_dir() == expected
    assert resolve_model_dir(DEFAULT_MODEL_SUBDIR) == expected


def test_semantic_ranker_can_select_cross_language_evidence_without_lexical_prefilter() -> None:
    backend = _FakeBackend("100 slots are occupied")

    result = rank_openvino_evidence(
        "排查数据库连接资源耗尽",
        {
            "distractor.log": "service startup completed normally",
            "service.log": "All 100 slots are occupied; new checkout calls are queued.",
        },
        backend=backend,
        min_similarity=0.8,
    )

    assert result.status == "OK"
    assert result.facts[0].source == "service.log"
    assert isinstance(result.facts[0].score, int)
    assert backend.query_inputs == ["排查数据库连接资源耗尽"]
    assert any("startup completed" in text for text in backend.document_inputs)


def test_semantic_ranker_does_not_release_below_threshold_context() -> None:
    result = rank_openvino_evidence(
        "payment outage",
        {"notes.md": "tomatoes need water in the afternoon"},
        backend=_FakeBackend(None),
        min_similarity=0.8,
    )

    assert result.facts == ()
    assert result.status == "NO_RELEVANT_CONTEXT"


@pytest.mark.parametrize(
    ("similarity", "expected_status"),
    ((0.70, "OK"), (0.699, "NO_RELEVANT_CONTEXT")),
)
def test_evidence_supported_similarity_floor_is_stable(
    similarity: float,
    expected_status: str,
) -> None:
    result = rank_openvino_evidence(
        "cross-language incident diagnosis",
        {"service.log": "跨语言故障证据"},
        backend=_SimilarityBackend(similarity),
    )

    assert result.status == expected_status


@pytest.mark.parametrize(
    ("similarity", "expected_status"),
    ((0.74, "OK"), (0.739, "NO_RELEVANT_CONTEXT")),
)
def test_semantic_only_similarity_floor_remains_conservative(
    similarity: float,
    expected_status: str,
) -> None:
    result = rank_openvino_evidence(
        "why did the system fail",
        {"notes.log": "opaque observation qxzv"},
        backend=_SimilarityBackend(similarity),
    )

    assert result.status == expected_status


def test_hybrid_ranking_prefers_diagnostic_evidence_and_rejects_benign_noise() -> None:
    class _MappedBackend:
        def embed_query(self, text: str) -> list[float]:  # noqa: ARG002
            return [1.0, 0.0]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            similarities = {
                "Resource pool reached maximum capacity": 0.75,
                "Request volume increased 12x": 0.75,
                "CSS bundle completed successfully": 0.79,
                "MIT License": 0.76,
            }
            return [
                [similarities[text], math.sqrt(1.0 - similarities[text] ** 2)] for text in texts
            ]

    result = rank_openvino_evidence(
        "为什么服务突然大量失败？",
        {
            "capacity.log": "Resource pool reached maximum capacity",
            "change.log": "Request volume increased 12x",
            "css.log": "CSS bundle completed successfully",
            "license.txt": "MIT License",
        },
        backend=_MappedBackend(),
    )

    assert [fact.source for fact in result.facts] == [
        "change.log",
        "capacity.log",
        "license.txt",
    ]
    assert all(fact.source != "css.log" for fact in result.facts)


def test_non_diagnostic_retrieval_does_not_apply_incident_benign_gate() -> None:
    result = rank_openvino_evidence(
        "find the build completion record",
        {"build.log": "CSS bundle completed successfully"},
        backend=_FakeBackend("completed successfully"),
        min_similarity=0.8,
    )

    assert [fact.source for fact in result.facts] == ["build.log"]


def test_non_diagnostic_retrieval_does_not_run_scope_calibration() -> None:
    backend = _FakeBackend("build completed")
    result = rank_openvino_evidence(
        "find the build completion record",
        {
            "a.log": "2026-01-01T00:00:00Z alpha INFO build completed",
            "b.log": "2026-01-01T00:00:01Z beta INFO cache refreshed",
            "c.log": "2026-01-01T00:00:02Z gamma INFO tests passed",
            "d.log": "2026-01-01T00:00:03Z delta INFO archive written",
        },
        backend=backend,
        min_similarity=0.8,
    )

    assert [fact.source for fact in result.facts] == ["a.log"]
    assert len(backend.document_inputs) == 4


def test_failure_vocabulary_alone_does_not_turn_lookup_into_diagnosis() -> None:
    backend = _FakeBackend("timeout configuration")
    result = rank_openvino_evidence(
        "find the timeout configuration record",
        {
            "a.log": "2026-01-01T00:00:00Z alpha INFO timeout configuration",
            "b.log": "2026-01-01T00:00:01Z beta INFO cache refreshed",
            "c.log": "2026-01-01T00:00:02Z gamma INFO tests passed",
            "d.log": "2026-01-01T00:00:03Z delta INFO archive written",
        },
        backend=backend,
        min_similarity=0.8,
    )

    assert [fact.source for fact in result.facts] == ["a.log"]
    assert len(backend.document_inputs) == 4


def test_high_confidence_scope_grounding_keeps_target_producer_facts_first() -> None:
    class _FieldedBackend:
        def embed_query(self, text: str) -> list[float]:  # noqa: ARG002
            return [1.0, 0.0]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            vectors = []
            for text in texts:
                if " " not in text:
                    similarity = 0.86 if text.startswith("checkout-") else 0.78
                else:
                    similarity = 0.74 if " checkout-" in text else 0.82
                vectors.append([similarity, math.sqrt(1.0 - similarity**2)])
            return vectors

    result = rank_openvino_evidence(
        "为什么结账服务突然大量失败？",
        {
            "01_target.log": (
                "2026-01-01T00:00:00Z checkout-api ERROR resource capacity exhausted"
            ),
            "02_target.log": ("2026-01-01T00:00:01Z checkout-api METRIC failure rate increased"),
            "03_target.log": (
                "2026-01-01T00:00:02Z checkout-worker WARN queue volume increased 8x"
            ),
            "11_noise.log": (
                "2026-01-01T00:00:03Z mobile ERROR validation failed due to missing input"
            ),
            "12_noise.log": "2026-01-01T00:00:04Z docs ERROR export queue stalled",
            "13_noise.log": "2026-01-01T00:00:05Z image ERROR worker pool reached capacity",
            "14_noise.log": "2026-01-01T00:00:06Z search ERROR request failures increased",
        },
        backend=_FieldedBackend(),
    )

    required = {"01_target.log", "02_target.log", "03_target.log"}
    selected = [fact.source for fact in result.facts]
    assert set(selected[:3]) == required
    assert required.issubset(selected)
    assert len([source for source in selected if source not in required]) <= 1


def test_scope_calibration_extends_only_to_same_producer_family() -> None:
    anchors = ("alpha-api", "alpha-worker", "frontend", "mobile", "search")
    similarities = (0.86, 0.79, 0.80, 0.78, 0.77)
    vectors = [[similarity, math.sqrt(1.0 - similarity**2)] for similarity in similarities]

    calibration = _scope_calibration([1.0, 0.0], anchors, vectors)

    assert calibration is not None
    assert {"alpha-api", "alpha-worker"}.issubset(calibration.supported_anchors)
    assert "frontend" not in calibration.supported_anchors
    assert calibration.affinities["alpha-worker"] == pytest.approx(
        calibration.affinities["alpha-api"]
    )
    assert "frontend" not in calibration.affinities


def test_near_duplicate_candidates_do_not_consume_multiple_fact_slots() -> None:
    class _DuplicateBackend:
        def embed_query(self, text: str) -> list[float]:  # noqa: ARG002
            return [1.0, 0.0]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:  # noqa: ARG002
            return [[1.0, 0.0], [0.9999, 0.0141], [0.8, 0.6]]

    result = rank_openvino_evidence(
        "find failure evidence",
        {
            "a.log": "ERROR worker failed during scheduled attempt 100 in checkout service",
            "b.log": "ERROR worker failed during scheduled attempt 101 in checkout service",
            "c.log": "FATAL queue unavailable",
        },
        backend=_DuplicateBackend(),
    )

    assert [fact.source for fact in result.facts] == ["a.log", "c.log"]


def test_semantic_ranker_covers_late_fragments_of_long_lines() -> None:
    marker = "late-fragment-marker"
    backend = _FakeBackend(marker)
    result = rank_openvino_evidence(
        "find the late signal",
        {"long.log": ("x" * 2_000) + marker},
        backend=backend,
        min_similarity=0.8,
    )

    assert result.status == "OK"
    assert result.facts[0].local_ref == "L1"
    assert marker in result.facts[0].text


def test_long_line_fragments_are_bounded_and_overlap_boundary_phrases() -> None:
    phrase = "diagnostic evidence crosses boundary"
    text = ("a" * 376) + phrase + ("b" * 400)

    fragments = _utf8_fragments(text, MAX_CHUNK_UTF8_BYTES)

    assert all(len(fragment.encode("utf-8")) <= MAX_CHUNK_UTF8_BYTES for fragment in fragments)
    assert any(phrase in fragment for fragment in fragments)


def test_token_counter_recursively_splits_pathological_fragments() -> None:
    fragments = _token_safe_fragments(
        "x" * 120,
        MAX_CHUNK_UTF8_BYTES,
        lambda value: len(value) * 10,
    )

    assert len(fragments) > 1
    assert all(len(fragment) * 10 <= 480 for fragment in fragments)


def test_blank_lines_split_semantic_paragraphs_without_becoming_candidates() -> None:
    candidates = _candidate_windows((("service.log", "first paragraph\n\nsecond paragraph"),))

    assert [candidate.text for candidate in candidates] == [
        "first paragraph",
        "second paragraph",
    ]


def test_candidate_windows_do_not_mix_structured_log_producers() -> None:
    candidates = _candidate_windows(
        (
            (
                "aggregate.log",
                "\n".join(
                    (
                        "2026-01-01T00:00:00Z alpha INFO first event",
                        "2026-01-01T00:00:01Z alpha WARN second event",
                        "2026-01-01T00:00:02Z beta ERROR third event",
                    )
                ),
            ),
        )
    )

    assert [candidate.text for candidate in candidates] == [
        "2026-01-01T00:00:00Z alpha INFO first event\n2026-01-01T00:00:01Z alpha WARN second event",
        "2026-01-01T00:00:02Z beta ERROR third event",
    ]


def test_long_line_fragments_inherit_the_structured_log_producer() -> None:
    line = "2026-01-01T00:00:00Z target-service ERROR " + ("x" * 600) + " late diagnostic evidence"

    candidates = _candidate_windows((("service.log", line),))

    assert len(candidates) > 1
    assert {_candidate_scope_anchor(candidate) for candidate in candidates} == {"target-service"}


@pytest.mark.parametrize(
    ("line", "expected"),
    (
        ('{"service":"checkout-api","level":"error"}', "checkout-api"),
        ("component=checkout-worker status=degraded", "checkout-worker"),
        ("2026-01-01T00:00:00Z checkout-api ERROR failed", "checkout-api"),
        (("x" * 65) + " ERROR failed", None),
        ("service=" + ("x" * 65) + " status=degraded", None),
        ("ordinary prose without structured producer metadata", None),
    ),
)
def test_scope_anchor_parses_generic_structured_log_forms(
    line: str,
    expected: str | None,
) -> None:
    assert _line_scope_anchor(line) == expected


def _write_valid_model_stub(root: Path) -> None:
    files: dict[str, dict[str, object]] = {}
    for filename in (
        "config.json",
        "openvino_model.bin",
        "openvino_model.xml",
        "openvino_tokenizer.bin",
        "openvino_tokenizer.xml",
        "special_tokens_map.json",
        "tokenizer_config.json",
    ):
        payload = f"stub:{filename}".encode()
        (root / filename).write_bytes(payload)
        files[filename] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    manifest = {
        "schema_version": "0.1",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "format": MODEL_FORMAT,
        "files": files,
        "installed_bytes": 0,
    }
    manifest_path = root / MANIFEST_FILENAME
    for _ in range(8):
        manifest_path.write_text(stable_json(manifest) + "\n", encoding="utf-8")
        measured = manifest_path.stat().st_size + sum(
            int(record["bytes"]) for record in files.values()
        )
        if measured == manifest["installed_bytes"]:
            break
        manifest["installed_bytes"] = measured


def test_model_manifest_detects_same_size_artifact_tampering(tmp_path: Path) -> None:
    _write_valid_model_stub(tmp_path)
    manifest = validate_model_dir(tmp_path, verify_hashes=True)
    assert manifest.model_id == MODEL_ID

    artifact = tmp_path / "openvino_model.bin"
    artifact.write_bytes(b"x" * artifact.stat().st_size)

    with pytest.raises(OpenVINORankingUnavailable, match="^OPENVINO_RANKING_UNAVAILABLE$"):
        validate_model_dir(tmp_path, verify_hashes=True)
