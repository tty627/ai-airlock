"""YAML policy loader with a small, explicit deterministic-v0.1 schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

import yaml

from airlock.ingestion import IngestionLimits


class PolicyError(Exception):
    """A stable policy failure that never embeds path or YAML content."""

    def __init__(self, code: str = "INVALID_POLICY") -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class PolicyTransform:
    pii: str
    secrets: str
    internal_ips: str


@dataclass(frozen=True, slots=True)
class PolicyBlock:
    private_keys: bool
    prompt_injection: bool
    credential_values: bool


@dataclass(frozen=True, slots=True)
class PolicyLimits:
    max_capsule_tokens: int
    max_files: int
    max_file_bytes: int = 1024 * 1024
    max_total_bytes: int = 10 * 1024 * 1024

    def to_ingestion_limits(self) -> IngestionLimits:
        return IngestionLimits(
            max_files=self.max_files,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
        )


@dataclass(frozen=True, slots=True)
class Policy:
    name: str
    transform: PolicyTransform
    block: PolicyBlock
    limits: PolicyLimits


_DEFAULT_DATA: Final[dict[str, Any]] = {
    "policy": {
        "name": "developer-default",
        "transform": {
            "pii": "pseudonymize",
            "secrets": "redact",
            "internal_ips": "pseudonymize",
        },
        "block": {
            "private_keys": True,
            "prompt_injection": True,
            "credential_values": True,
        },
        "limits": {
            "max_capsule_tokens": 4000,
            "max_files": 100,
            "max_file_bytes": 1024 * 1024,
            "max_total_bytes": 10 * 1024 * 1024,
        },
    }
}


def _expect_mapping(
    value: object, keys: set[str], *, required: set[str] | None = None
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PolicyError()
    actual = set(value)
    required_keys = keys if required is None else required
    if not required_keys.issubset(actual) or not actual.issubset(keys):
        raise PolicyError()
    if not all(isinstance(key, str) for key in value):
        raise PolicyError()
    return value


def _positive_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PolicyError()
    return value


def _required_true(value: object) -> bool:
    if value is not True:
        raise PolicyError()
    return True


def _choice(value: object, allowed: set[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise PolicyError()
    return value


def _validate(data: object) -> Policy:
    root = _expect_mapping(data, {"policy"})
    policy_data = _expect_mapping(root["policy"], {"name", "transform", "block", "limits"})
    name = policy_data["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 128:
        raise PolicyError()

    transform_data = _expect_mapping(policy_data["transform"], {"pii", "secrets", "internal_ips"})
    transform = PolicyTransform(
        pii=_choice(transform_data["pii"], {"pseudonymize", "redact"}),
        # Secrets can never be configured to cross the local boundary raw.
        secrets=_choice(transform_data["secrets"], {"redact"}),
        internal_ips=_choice(transform_data["internal_ips"], {"pseudonymize", "redact"}),
    )

    block_data = _expect_mapping(
        policy_data["block"],
        {"private_keys", "prompt_injection", "credential_values"},
    )
    block = PolicyBlock(
        private_keys=_required_true(block_data["private_keys"]),
        prompt_injection=_required_true(block_data["prompt_injection"]),
        credential_values=_required_true(block_data["credential_values"]),
    )

    limit_keys = {
        "max_capsule_tokens",
        "max_files",
        "max_file_bytes",
        "max_total_bytes",
    }
    limits_data = _expect_mapping(
        policy_data["limits"],
        limit_keys,
        required={"max_capsule_tokens", "max_files"},
    )
    limits = PolicyLimits(
        max_capsule_tokens=_positive_integer(limits_data["max_capsule_tokens"]),
        max_files=_positive_integer(limits_data["max_files"]),
        max_file_bytes=_positive_integer(limits_data.get("max_file_bytes", 1024 * 1024)),
        max_total_bytes=_positive_integer(limits_data.get("max_total_bytes", 10 * 1024 * 1024)),
    )
    if limits.max_total_bytes < limits.max_file_bytes:
        raise PolicyError()
    return Policy(name=name.strip(), transform=transform, block=block, limits=limits)


def _default_policy_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "default_policy.yaml"


def load_policy(path: str | Path | None = None) -> Policy:
    """Load and strictly validate a UTF-8 YAML policy with ``safe_load``."""

    if path is None:
        default_path = _default_policy_path()
        if not default_path.is_file():
            return _validate(_DEFAULT_DATA)
        requested = default_path
    else:
        try:
            requested = Path(path)
        except TypeError:
            raise PolicyError() from None

    try:
        if requested.is_symlink() or not requested.is_file():
            raise PolicyError()
        raw = requested.read_text(encoding="utf-8-sig")
        data = yaml.safe_load(raw)
    except PolicyError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError):
        raise PolicyError() from None
    return _validate(data)
