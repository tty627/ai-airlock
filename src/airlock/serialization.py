"""Canonical serialization helpers."""

from __future__ import annotations

import json
from typing import Any


def stable_json(value: Any) -> str:
    """Serialize a public value deterministically without ASCII escaping."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def estimate_tokens(value: str | dict[str, Any]) -> int:
    """Return the documented deterministic UTF-8 byte estimate."""

    text = stable_json(value) if isinstance(value, dict) else value
    return (len(text.encode("utf-8")) + 3) // 4
