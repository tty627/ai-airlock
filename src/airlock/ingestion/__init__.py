"""Deterministic, fail-closed text ingestion."""

from .loader import (
    DEFAULT_LIMITS,
    SUPPORTED_EXTENSIONS,
    IngestionLimits,
    IngestionResult,
    InputIncomplete,
    LoadedFile,
    is_supported_text_file,
    load_path,
)

__all__ = [
    "DEFAULT_LIMITS",
    "SUPPORTED_EXTENSIONS",
    "IngestionLimits",
    "IngestionResult",
    "InputIncomplete",
    "LoadedFile",
    "is_supported_text_file",
    "load_path",
]
