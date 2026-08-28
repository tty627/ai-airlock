from __future__ import annotations

import hashlib
import json
from pathlib import Path

from airlock.capsule.redactor import transform_text
from airlock.detectors import detect_injections, detect_secrets
from airlock.pipeline import analyze
from airlock.serialization import stable_json

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "security_p0_holdout_v1.json"
FIXTURE_SHA256 = "5a9b2c6924350ab5284da585f3eab50338269e2f82117e66d8ae5838d1afb319"


def _holdout() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_security_p0_holdout_is_frozen_and_independent_from_benchmark() -> None:
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256
    assert FIXTURE.parent == ROOT / "tests" / "fixtures"
    assert "benchmark" not in FIXTURE.parts


def test_frozen_secret_grammar_and_task_markers_are_detected_by_explicit_oracle() -> None:
    holdout = _holdout()

    for case in holdout["secret_cases"]:
        findings = detect_secrets(case["text"], f"{case['id']}.txt")
        observed = [
            (finding.type, case["text"][finding.span.start : finding.span.end])
            for finding in findings
        ]
        assert (case["expected_type"], case["value"]) in observed

    for case in holdout["task_marker_cases"]:
        findings = detect_secrets(case["text"], f"{case['id']}.txt")
        observed_values = {
            case["text"][finding.span.start : finding.span.end] for finding in findings
        }
        assert case["value"] in observed_values
        assert all(finding.type == "API_KEY" for finding in findings)

    for text in holdout["benign_secret_cases"]:
        assert detect_secrets(text, "benign.txt") == []


def test_frozen_injection_variants_are_classified_and_whole_lines_are_quarantined() -> None:
    holdout = _holdout()

    for case in holdout["injection_cases"]:
        findings = detect_injections(case["text"], f"{case['id']}.md")
        if case["label"] == "benign":
            assert findings == []
            continue
        assert any(finding.type == "PROMPT_INJECTION" for finding in findings)
        transformed = transform_text(case["text"], findings)
        assert transformed.text == "[UNTRUSTED_INSTRUCTION_ISOLATED]"
        assert case["text"] not in transformed.text


def test_high_relevance_never_overrides_quarantine_or_decision(tmp_path: Path) -> None:
    holdout = _holdout()
    malicious = [case for case in holdout["injection_cases"] if case["label"] == "malicious"]
    workspace = tmp_path / "mixed"
    workspace.mkdir()
    (workspace / "safe.log").write_text(
        "ERROR payment 503 root cause: Redis pool exhausted after retry traffic increased.\n",
        encoding="utf-8",
    )
    for index, case in enumerate(malicious):
        (workspace / f"attack_{index}.md").write_text(case["text"] + "\n", encoding="utf-8")

    result = analyze(task="payment 503 timeout root cause retry", path=workspace)
    public = stable_json(result)

    assert result["decision"] == "ALLOW_WITH_TRANSFORM"
    assert result["security"]["prompt_injections"] >= len(malicious)
    assert result["security"]["blocked_instructions"] == len(malicious)
    assert "Redis pool exhausted" in public
    for case in malicious:
        assert case["text"] not in public


def test_attack_only_holdouts_fail_closed_with_no_safe_context(tmp_path: Path) -> None:
    holdout = _holdout()
    malicious = [case for case in holdout["injection_cases"] if case["label"] == "malicious"]

    for index, case in enumerate(malicious):
        workspace = tmp_path / f"attack-only-{index}"
        workspace.mkdir()
        (workspace / "attack.md").write_text(case["text"], encoding="utf-8")
        result = analyze(task="payment timeout root cause", path=workspace)

        assert result["decision"] == "BLOCK"
        assert result["safe_context"]["facts"] == []
        assert result["safe_context"]["coverage_warning"] == "NO_SAFE_CONTEXT"
        assert case["text"] not in stable_json(result)


def test_task_specific_token_marker_is_redacted_before_task_or_capsule_release(
    tmp_path: Path,
) -> None:
    marker = "FINAL_REVIEW_TOKEN_Z7K4P9X2"
    (tmp_path / "safe.log").write_text(
        "ERROR payment timeout after Redis pool exhaustion.\n",
        encoding="utf-8",
    )

    result = analyze(task=f"Diagnose payment timeout for marker {marker}", path=tmp_path)
    public = stable_json(result)

    assert marker not in public
    assert "[API_KEY_REDACTED]" in result["task"]
    assert result["privacy"]["raw_sensitive_spans_forwarded"] == 0
