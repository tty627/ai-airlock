from __future__ import annotations

from pathlib import Path

import pytest

from airlock.policy import PolicyError, load_policy

ROOT = Path(__file__).resolve().parents[2]


def test_default_and_demo_policies_are_safe_and_valid() -> None:
    default = load_policy()
    demo = load_policy(ROOT / "config" / "demo_policy.yaml")

    for policy in (default, demo):
        assert policy.transform.secrets == "redact"
        assert policy.transform.pii == "pseudonymize"
        assert policy.block.prompt_injection is True
        assert policy.limits.max_capsule_tokens == 4000
        assert policy.limits.to_ingestion_limits().max_files == 100


def test_policy_rejects_unknown_fields(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """policy:
  name: unsafe
  unknown: value
  transform: {pii: pseudonymize, secrets: redact, internal_ips: pseudonymize}
  block: {private_keys: true, prompt_injection: true, credential_values: true}
  limits: {max_capsule_tokens: 4000, max_files: 100}
""",
        encoding="utf-8",
    )

    with pytest.raises(PolicyError, match="^INVALID_POLICY$"):
        load_policy(policy)


@pytest.mark.parametrize(
    "replacement",
    [
        "secrets: allow",
        "secrets: 123",
        "secrets: pseudonymize",
    ],
)
def test_policy_cannot_allow_raw_secrets(tmp_path: Path, replacement: str) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        f"""policy:
  name: test
  transform:
    pii: pseudonymize
    {replacement}
    internal_ips: pseudonymize
  block:
    private_keys: true
    prompt_injection: true
    credential_values: true
  limits:
    max_capsule_tokens: 4000
    max_files: 100
""",
        encoding="utf-8",
    )

    with pytest.raises(PolicyError):
        load_policy(policy)


def test_policy_rejects_boolean_as_integer_and_bad_yaml(tmp_path: Path) -> None:
    bad_type = tmp_path / "type.yaml"
    bad_type.write_text(
        """policy:
  name: test
  transform: {pii: pseudonymize, secrets: redact, internal_ips: pseudonymize}
  block: {private_keys: true, prompt_injection: true, credential_values: true}
  limits: {max_capsule_tokens: true, max_files: 100}
""",
        encoding="utf-8",
    )
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("policy: [", encoding="utf-8")

    with pytest.raises(PolicyError):
        load_policy(bad_type)
    with pytest.raises(PolicyError):
        load_policy(malformed)


def test_policy_failure_does_not_echo_path_or_content(tmp_path: Path) -> None:
    policy = tmp_path / "sensitive-policy-name.yaml"
    policy.write_text("secret-content", encoding="utf-8")

    with pytest.raises(PolicyError) as captured:
        load_policy(policy)

    assert str(captured.value) == "INVALID_POLICY"
    assert "sensitive" not in str(captured.value)
    assert "secret-content" not in str(captured.value)


def test_policy_safe_load_rejects_python_object_tags(tmp_path: Path) -> None:
    policy = tmp_path / "object.yaml"
    policy.write_text("!!python/object/apply:os.system ['echo unsafe']", encoding="utf-8")

    with pytest.raises(PolicyError, match="^INVALID_POLICY$"):
        load_policy(policy)


@pytest.mark.parametrize("field", ["private_keys", "prompt_injection", "credential_values"])
def test_mandatory_security_boundaries_cannot_be_disabled(tmp_path: Path, field: str) -> None:
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        f"""policy:
  name: unsafe
  transform: {{pii: pseudonymize, secrets: redact, internal_ips: pseudonymize}}
  block:
    private_keys: {str(field != "private_keys").lower()}
    prompt_injection: {str(field != "prompt_injection").lower()}
    credential_values: {str(field != "credential_values").lower()}
  limits: {{max_capsule_tokens: 4000, max_files: 100}}
""",
        encoding="utf-8",
    )

    with pytest.raises(PolicyError):
        load_policy(policy)
