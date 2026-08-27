"""Safe, deterministic ingestion of a local text file or directory tree.

The loader deliberately returns content snapshots rather than open paths.  A
supported file that cannot be read completely aborts the whole operation; a
caller must never mistake a partial workspace for a complete scan.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final

SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".bash",
        ".c",
        ".cfg",
        ".conf",
        ".cpp",
        ".csv",
        ".go",
        ".h",
        ".hpp",
        ".htm",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".json",
        ".jsonl",
        ".jsx",
        ".log",
        ".markdown",
        ".md",
        ".php",
        ".properties",
        ".ps1",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".toml",
        ".ts",
        ".tsv",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
        ".zsh",
    }
)


class InputIncomplete(Exception):
    """A fail-closed input error with a non-sensitive, stable error code."""

    def __init__(self, code: str = "INPUT_INCOMPLETE") -> None:
        self.code = code
        super().__init__(code)


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class IngestionLimits:
    """Hard limits applied before any input is released downstream."""

    max_files: int = 100
    max_file_bytes: int = 1024 * 1024
    max_total_bytes: int = 10 * 1024 * 1024

    def __post_init__(self) -> None:
        _positive_int(self.max_files, "max_files")
        _positive_int(self.max_file_bytes, "max_file_bytes")
        _positive_int(self.max_total_bytes, "max_total_bytes")
        if self.max_total_bytes < self.max_file_bytes:
            raise ValueError("max_total_bytes must be at least max_file_bytes")


DEFAULT_LIMITS: Final[IngestionLimits] = IngestionLimits()


@dataclass(frozen=True, slots=True)
class LoadedFile:
    """An immutable UTF-8 text snapshot with local, relative provenance."""

    relative_path: str
    text: str
    byte_size: int

    @property
    def source(self) -> str:
        """Alias used by downstream evidence/capsule components."""

        return self.relative_path


@dataclass(frozen=True, slots=True)
class IngestionResult:
    files: tuple[LoadedFile, ...]
    skipped_files: int
    total_bytes: int

    @property
    def inspected_files(self) -> int:
        return len(self.files)

    @property
    def documents(self) -> dict[str, str]:
        """Return a fresh insertion-ordered mapping in stable path order."""

        return {item.relative_path: item.text for item in self.files}


def is_supported_text_file(path: str | Path) -> bool:
    """Return whether *path* has an allowlisted text name.

    ``.env`` and every ``.env.*`` variant are intentionally recognized even
    though ``Path.suffix`` would classify the latter as (for example)
    ``.example``.
    """

    name = Path(path).name.lower()
    return name == ".env" or name.startswith(".env.") or Path(name).suffix in SUPPORTED_EXTENSIONS


def _safe_relative(path: Path, root: Path) -> str:
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise InputIncomplete() from None
    return relative.as_posix()


def _collect_directory(root_path: Path, root: Path) -> tuple[list[tuple[str, Path]], int]:
    candidates: list[tuple[str, Path]] = []
    skipped = 0

    def abort_walk(_error: OSError) -> None:
        raise InputIncomplete()

    try:
        walker = os.walk(root_path, topdown=True, onerror=abort_walk, followlinks=False)
        for directory, directory_names, file_names in walker:
            directory_path = Path(directory)

            retained_directories: list[str] = []
            for name in sorted(directory_names):
                candidate = directory_path / name
                try:
                    if candidate.is_symlink():
                        skipped += 1
                    else:
                        retained_directories.append(name)
                except OSError:
                    raise InputIncomplete() from None
            directory_names[:] = retained_directories

            for name in sorted(file_names):
                candidate = directory_path / name
                try:
                    metadata = candidate.lstat()
                except OSError:
                    raise InputIncomplete() from None

                if stat.S_ISLNK(metadata.st_mode):
                    skipped += 1
                    continue
                if not stat.S_ISREG(metadata.st_mode):
                    skipped += 1
                    continue

                relative = _safe_relative(candidate, root)
                if is_supported_text_file(candidate):
                    candidates.append((relative, candidate))
                else:
                    skipped += 1
    except InputIncomplete:
        raise
    except OSError:
        raise InputIncomplete() from None

    candidates.sort(key=lambda item: item[0])
    return candidates, skipped


def _read_utf8_file(path: Path, limits: IngestionLimits) -> tuple[str, int]:
    descriptor = -1
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limits.max_file_bytes:
            raise InputIncomplete()
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            payload = stream.read(limits.max_file_bytes + 1)
            after = os.fstat(stream.fileno())
    except InputIncomplete:
        raise
    except OSError:
        raise InputIncomplete() from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    if len(payload) > limits.max_file_bytes:
        raise InputIncomplete()
    # A concurrent replacement or append makes the snapshot ambiguous.  Fail
    # closed instead of claiming a stable, complete scan.
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or after.st_size != len(payload)
    ):
        raise InputIncomplete()
    try:
        return payload.decode("utf-8-sig"), len(payload)
    except UnicodeDecodeError:
        raise InputIncomplete() from None


def load_path(
    path: str | os.PathLike[str],
    limits: IngestionLimits | None = None,
) -> IngestionResult:
    """Load an allowlisted file or directory without following symlinks.

    Paths in the result are POSIX-style and relative to a directory root.  For
    a single-file invocation, the source is just the file name.  Unknown file
    types are counted as skipped; any failure involving a supported file raises
    :class:`InputIncomplete` before a result is returned.
    """

    active_limits = limits or DEFAULT_LIMITS
    if not isinstance(active_limits, IngestionLimits):
        raise TypeError("limits must be IngestionLimits")
    try:
        requested = Path(path)
    except TypeError:
        raise InputIncomplete() from None

    try:
        if requested.is_symlink():
            raise InputIncomplete()
        metadata = requested.stat()
        resolved = requested.resolve(strict=True)
    except InputIncomplete:
        raise
    except (OSError, RuntimeError):
        raise InputIncomplete() from None

    skipped = 0
    if stat.S_ISDIR(metadata.st_mode):
        candidates, skipped = _collect_directory(requested, resolved)
    elif stat.S_ISREG(metadata.st_mode):
        if is_supported_text_file(requested):
            candidates = [(requested.name, requested)]
        else:
            candidates = []
            skipped = 1
    else:
        raise InputIncomplete()

    if len(candidates) > active_limits.max_files:
        raise InputIncomplete()

    snapshots: list[LoadedFile] = []
    total_bytes = 0
    for relative_path, candidate in candidates:
        # Re-check containment immediately before the read to narrow races.
        if stat.S_ISDIR(metadata.st_mode):
            _safe_relative(candidate, resolved)
        text, byte_size = _read_utf8_file(candidate, active_limits)
        total_bytes += byte_size
        if total_bytes > active_limits.max_total_bytes:
            raise InputIncomplete()
        snapshots.append(LoadedFile(relative_path=relative_path, text=text, byte_size=byte_size))

    return IngestionResult(
        files=tuple(snapshots),
        skipped_files=skipped,
        total_bytes=total_bytes,
    )
