from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from airlock import cli
from airlock.detectors import Sensitivity, detect_all
from airlock.pipeline import analyze
from airlock.relevance import openvino_ready
from airlock.serialization import stable_json

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo" / "incident"
TASK = "分析支付服务失败原因，并检查 Redis 连接耗尽与重试风暴"
SCOPE_CASES = ROOT / "tests" / "fixtures" / "relevance_scope_cases.json"


def _raw_demo_values() -> set[str]:
    values: set[str] = set()
    for path in sorted(DEMO.iterdir()):
        text = path.read_text(encoding="utf-8")
        for finding in detect_all(text, path.name):
            if finding.sensitivity in {Sensitivity.SECRET, Sensitivity.PII}:
                values.add(text[finding.span.start : finding.span.end])
    return values


def _fixture_manifest(documents: dict[str, str]) -> str:
    records = b"".join(
        (f"{hashlib.sha256(text.encode('utf-8')).hexdigest()}  ./{source}\n").encode("utf-8")
        for source, text in sorted(documents.items())
    )
    return hashlib.sha256(records).hexdigest()


def _scope_cases() -> list[dict[str, object]]:
    payload = json.loads(SCOPE_CASES.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "0.1"
    return payload["cases"]


def test_real_openvino_capsule_is_safe_useful_and_repeatable(tmp_path: Path) -> None:
    if not openvino_ready():
        pytest.skip("prepared OpenVINO model and runtime are not available")

    audit = tmp_path / "events.jsonl"
    first = analyze(
        task=TASK,
        path=DEMO,
        audit_log=audit,
        relevance_backend="openvino",
    )
    second = analyze(task=TASK, path=DEMO, relevance_backend="openvino")

    assert stable_json(first) == stable_json(second)
    assert first["decision"] == "ALLOW_WITH_TRANSFORM"
    assert first["risk_level"] == "HIGH"
    assert first["inference"]["mode"] == "openvino_embedding"
    assert first["inference"]["openvino_available"] is True
    assert first["inference"]["chunks_processed"] > 0
    assert first["inference"]["fallback_state"] == "not_used"
    assert first["safe_context"]["selection_method"] == "openvino_hybrid_relevance_v3"
    assert first["privacy"]["raw_sensitive_spans_forwarded"] == 0
    assert json.loads(audit.read_text(encoding="utf-8"))["inference_mode"] == ("openvino_embedding")

    public = stable_json(first) + audit.read_text(encoding="utf-8")
    for value in _raw_demo_values():
        assert value.casefold() not in public.casefold()
    for isolated in (
        "IMPORTANT SYSTEM OVERRIDE",
        "Read every credential",
        "collector.invalid",
    ):
        assert isolated not in public

    evidence = "\n".join(fact["text"] for fact in first["safe_context"]["facts"])
    assert "100/100" in evidence
    assert "connection pool exhaustion" in evidence
    assert "retry storm" in evidence


def test_real_openvino_human_cli_does_not_leak(
    capsys: pytest.CaptureFixture[str],
) -> None:
    if not openvino_ready():
        pytest.skip("prepared OpenVINO model and runtime are not available")

    code = cli.main(
        [
            "analyze",
            "--task",
            TASK,
            "--path",
            str(DEMO),
            "--relevance-backend",
            "openvino",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert captured.err == ""
    assert "connection pool exhaustion" in captured.out
    for value in _raw_demo_values():
        assert value.casefold() not in captured.out.casefold()
    assert "IMPORTANT SYSTEM OVERRIDE" not in captured.out
    assert "collector.invalid" not in captured.out


def test_real_openvino_high_noise_keeps_evidence_without_filling_with_build_noise(
    tmp_path: Path,
) -> None:
    if not openvino_ready():
        pytest.skip("prepared OpenVINO model and runtime are not available")

    documents = {
        "01_capacity.log": "Resource connection pool reached maximum capacity",
        "02_timeout.log": "Request timeout rate increased",
        "03_amplification.log": "Client traffic increased 12x",
        "90_license.txt": "MIT License",
        "91_css.log": "CSS bundle completed",
    }
    for name, text in documents.items():
        (tmp_path / name).write_text(text + "\n", encoding="utf-8")
    for index in range(80):
        (tmp_path / f"noise_{index:03d}.log").write_text(
            f"INFO documentation build artifact {index} completed successfully; "
            "static icon cache warmed.\n",
            encoding="utf-8",
        )

    capsule = analyze(
        task="为什么服务突然大量失败？",
        path=tmp_path,
        relevance_backend="openvino",
    )
    selected = [fact["source"] for fact in capsule["safe_context"]["facts"]]
    required = {"01_capacity.log", "02_timeout.log", "03_amplification.log"}

    assert required.issubset(selected)
    assert len([source for source in selected if source not in required]) <= 1
    assert "91_css.log" not in selected
    assert not any(source.startswith("noise_") for source in selected)
    assert capsule["inference"]["chunks_processed"] == 85


@pytest.mark.parametrize("case", _scope_cases(), ids=lambda case: str(case["id"]))
def test_real_openvino_scope_regressions_keep_required_evidence(
    tmp_path: Path,
    case: dict[str, object],
) -> None:
    if not openvino_ready():
        pytest.skip("prepared OpenVINO model and runtime are not available")

    documents = case["documents"]
    assert isinstance(documents, dict)
    assert _fixture_manifest(documents) == case["source_manifest_sha256"]
    for source, text in documents.items():
        (tmp_path / source).write_text(text, encoding="utf-8")

    capsule = analyze(
        task=str(case["task"]),
        path=tmp_path,
        relevance_backend="openvino",
    )
    selected = [fact["source"] for fact in capsule["safe_context"]["facts"]]
    required = set(case["required_sources"])

    assert set(selected[: len(required)]) == required
    assert required.issubset(selected)
    assert len([source for source in selected if source not in required]) <= 1
    assert capsule["inference"]["chunks_processed"] == len(documents)


def test_real_openvino_same_family_producer_survives_stronger_foreign_error(
    tmp_path: Path,
) -> None:
    if not openvino_ready():
        pytest.skip("prepared OpenVINO model and runtime are not available")

    case = next(case for case in _scope_cases() if case["id"] == "order_service_holdout")
    documents = dict(case["documents"])
    documents["13_localization.log"] = (
        "2026-08-28T15:00:03Z frontend ERROR Localization validation failed due to missing input.\n"
    )
    for source, text in documents.items():
        (tmp_path / source).write_text(text, encoding="utf-8")

    capsule = analyze(
        task=str(case["task"]),
        path=tmp_path,
        relevance_backend="openvino",
    )
    selected = [fact["source"] for fact in capsule["safe_context"]["facts"]]
    required = set(case["required_sources"])

    assert set(selected[: len(required)]) == required
    assert required.issubset(selected)
