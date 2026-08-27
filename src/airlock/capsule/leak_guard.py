"""Final fail-closed guard for every externally visible payload."""

from __future__ import annotations

import re
from collections.abc import Iterable

from airlock.errors import LeakageGuardError

_DIGITS_RE = re.compile(r"\D+")


def _variants(value: str) -> tuple[str, ...]:
    variants = {value.casefold()}
    digits = _DIGITS_RE.sub("", value)
    if len(digits) >= 7:
        variants.add(digits)
    return tuple(item for item in variants if len(item) >= 4)


def find_sensitive_leaks(payloads: Iterable[str], sensitive_values: Iterable[str]) -> int:
    """Count distinct source values that remain in any public payload."""

    folded_payloads = tuple(payload.casefold() for payload in payloads)
    digit_payloads = tuple(_DIGITS_RE.sub("", payload) for payload in payloads)
    leaked = 0
    for value in set(sensitive_values):
        matched = False
        for variant in _variants(value):
            haystacks = digit_payloads if variant.isdigit() else folded_payloads
            if any(variant in payload for payload in haystacks):
                matched = True
                break
        leaked += int(matched)
    return leaked


def enforce_no_sensitive_leaks(payloads: Iterable[str], sensitive_values: Iterable[str]) -> None:
    if find_sensitive_leaks(payloads, sensitive_values):
        raise LeakageGuardError()
