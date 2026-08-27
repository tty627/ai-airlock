"""Public interface for AI Airlock's deterministic detectors."""

from __future__ import annotations

from .injection import detect_injections
from .models import Action, InternalFinding, Sensitivity, Span
from .overlap import TYPE_PRIORITY, resolve_overlaps, resolve_sensitive_overlaps
from .pii import detect_pii
from .secrets import detect_secrets


def detect_all(text: str, source: str = "<input>") -> list[InternalFinding]:
    """Run every deterministic detector and return stable, resolved findings."""

    return resolve_overlaps(
        [
            *detect_secrets(text, source),
            *detect_pii(text, source),
            *detect_injections(text, source),
        ]
    )


__all__ = [
    "Action",
    "InternalFinding",
    "Sensitivity",
    "Span",
    "TYPE_PRIORITY",
    "detect_all",
    "detect_injections",
    "detect_pii",
    "detect_secrets",
    "resolve_overlaps",
    "resolve_sensitive_overlaps",
]
