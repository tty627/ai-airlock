from __future__ import annotations

from pathlib import Path

from airlock.detectors import Sensitivity, detect_all
from airlock.pipeline import analyze, scan
from airlock.serialization import stable_json

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo" / "incident"


def _raw_sensitive_values() -> set[str]:
    values: set[str] = set()
    for path in sorted(DEMO.iterdir()):
        text = path.read_text(encoding="utf-8")
        for finding in detect_all(text, path.name):
            if finding.sensitivity in {Sensitivity.SECRET, Sensitivity.PII}:
                values.add(text[finding.span.start : finding.span.end])
    return values


def test_sensitive_and_malicious_demo_values_never_leave_public_outputs(
    tmp_path: Path,
) -> None:
    audit = tmp_path / "audit.jsonl"
    scan_result = scan(path=DEMO)
    capsule = analyze(
        task="Analyze the payment failure",
        path=DEMO,
        audit_log=audit,
    )
    payload = "\n".join(
        (stable_json(scan_result), stable_json(capsule), audit.read_text(encoding="utf-8"))
    )

    for value in _raw_sensitive_values():
        assert value.casefold() not in payload.casefold()
    assert "IMPORTANT SYSTEM OVERRIDE" not in payload
    assert "collector.invalid" not in payload
    assert "Read every credential" not in payload
    assert str(DEMO.resolve()) not in payload
    assert "Analyze the payment failure" not in audit.read_text(encoding="utf-8")


def test_sensitive_filename_is_transformed_in_facts_and_findings(tmp_path: Path) -> None:
    source = tmp_path / "alice@example.com.log"
    source.write_text("ERROR payment failed", encoding="utf-8")

    scan_result = scan(path=tmp_path)
    capsule = analyze(task="analyze payment failure", path=tmp_path)
    public = stable_json(scan_result) + stable_json(capsule)

    assert "alice@example.com" not in public
    assert "[EMAIL_001]" in public


def test_public_policy_override_changes_pipeline_transforms(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "service.log").write_text(
        "ERROR owner=alice@example.com host=192.0.2.4",
        encoding="utf-8",
    )
    policy = tmp_path / "strict.yaml"
    policy.write_text(
        """policy:
  name: strict-redaction
  transform: {pii: redact, secrets: redact, internal_ips: redact}
  block: {private_keys: true, prompt_injection: true, credential_values: true}
  limits: {max_capsule_tokens: 4000, max_files: 100}
""",
        encoding="utf-8",
    )

    result = analyze(task="analyze error", path=workspace, policy_path=policy)
    public = stable_json(result)

    assert "[EMAIL_REDACTED]" in public
    assert "[IPV4_REDACTED]" in public
    assert "alice@example.com" not in public
    assert "192.0.2.4" not in public
