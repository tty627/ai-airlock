"""Optional OpenVINO embedding challenger for already-sanitized text.

The imports for OpenVINO are intentionally lazy.  Installing or removing the
optional runtime must not change the deterministic lexical path.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any, Callable, Mapping, Protocol, Sequence

from airlock.relevance.ranker import (
    RankedFact,
    RankingError,
    RankingResult,
    _facts_token_estimate,
    _line_score,
    _normalize_documents,
    estimate_tokens,
    tokenize,
)

MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
MODEL_FORMAT = "openvino_ir_fp16_with_tokenizer"
DEFAULT_MODEL_SUBDIR = "models/multilingual-e5-small-openvino-fp16"
MODEL_DIR_ENV = "AI_AIRLOCK_EMBEDDING_MODEL_DIR"
MODEL_CACHE_ENV = "AI_AIRLOCK_MODEL_CACHE"
MANIFEST_FILENAME = "model_manifest.json"
MODEL_SIZE_LIMIT_BYTES = 500_000_000

SELECTION_METHOD = "openvino_hybrid_relevance_v3"
INFERENCE_MODE = "openvino_embedding"
DEVICE = "CPU"
QUERY_INSTRUCTION = "query: "
DOCUMENT_INSTRUCTION = "passage: "

MAX_INPUT_TOKENS = 512
MAX_DOCUMENT_TOKENS = 480
# A byte bound is intentionally conservative because the model accepts at most
# 512 tokens and some punctuation-heavy inputs approach one token per byte.
# The overlap prevents a diagnostic phrase crossing a fragment boundary from
# being split out of both embeddings.
MAX_CHUNK_UTF8_BYTES = 256
CHUNK_OVERLAP_UTF8_BYTES = 64
MAX_CHUNK_LINES = 5
MAX_CANDIDATE_WINDOWS = 1_024
DEFAULT_MAX_FACTS = 8
# multilingual-e5-small similarities occupy a narrow high range; this floor is
# calibrated on synthetic incident retrieval and remains a conservative opt-in
# challenger setting, not a universal semantic-relevance guarantee.
DEFAULT_MIN_SIMILARITY = 0.74
SUPPORTED_MIN_SIMILARITY = 0.70
MAX_NEUTRAL_FACTS = 1
MAX_OUT_OF_SCOPE_FACTS = 1
NEAR_DUPLICATE_SIMILARITY = 0.98
NEAR_DUPLICATE_TOKEN_JACCARD = 0.80
EMBEDDING_BATCH_SIZE = 32

# Fielded scope grounding is activated only when a diagnostic input contains
# several distinct structured-log producers and the pinned model separates one
# producer cluster from the rest.  This prevents generic failure vocabulary in
# unrelated services from filling the evidence budget while leaving ordinary
# prose and low-diversity inputs on the existing hybrid path.
MIN_SCOPE_ANCHORS = 4
SCOPE_MIN_TOP_SIMILARITY = 0.78
SCOPE_MIN_CONTRAST = 0.035
SCOPE_KEEP_MARGIN = 0.025
SCOPE_AFFINITY_WEIGHT = 1_000_000

_REQUIRED_MODEL_FILES = frozenset(
    {
        "config.json",
        "openvino_model.bin",
        "openvino_model.xml",
        "openvino_tokenizer.bin",
        "openvino_tokenizer.xml",
        "special_tokens_map.json",
        "tokenizer_config.json",
    }
)
_ISOLATED_INSTRUCTION = "[UNTRUSTED_INSTRUCTION_ISOLATED]"
_LOG_LEVELS = frozenset(
    {
        "ALERT",
        "CRITICAL",
        "DEBUG",
        "EMERGENCY",
        "ERROR",
        "FATAL",
        "INFO",
        "METRIC",
        "NOTICE",
        "TRACE",
        "WARN",
        "WARNING",
    }
)
_SCOPE_FIELD = re.compile(
    r"(?:^|[\s,{])(?:[\"']?)(?:app(?:lication)?|component|module|service|subsystem)"
    r"(?:[\"']?)\s*[:=]\s*(?:[\"']?)([A-Za-z][A-Za-z0-9_.:/-]{0,63})"
    r"(?![A-Za-z0-9_.:/-])",
    re.IGNORECASE,
)
_SCOPE_ANCHOR = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]{0,63}$")
_TIMESTAMP_TOKEN = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}(?:[T ][0-9:.+-]+Z?)?|\d{2}:\d{2}:\d{2}(?:\.\d+)?)$"
)
_IDENTIFIER_SEPARATOR = re.compile(r"[._:/-]+")
_PRODUCER_ROLE_TOKENS = frozenset(
    {
        "api",
        "app",
        "application",
        "backend",
        "client",
        "consumer",
        "daemon",
        "frontend",
        "gateway",
        "job",
        "node",
        "processor",
        "server",
        "service",
        "subsystem",
        "worker",
    }
)

# These patterns describe task intent and generic diagnostic evidence.  They
# deliberately avoid product, service, datastore, and incident-specific nouns.
_DIAGNOSTIC_TASK = re.compile(
    r"\b(?:why|cause|explain|diagnos(?:e|is|tic)|determine|identify|root\s+cause)\b"
    r"|(?:为什么|为何|原因|根因|诊断|排查|解释)",
    re.IGNORECASE,
)
_CHANGE_SIGNAL = re.compile(
    r"\b(?:increase(?:d|s|ing)?|rose|risen|grew|growing|surge(?:d|s|ing)?|"
    r"spike(?:d|s|ing)?|jump(?:ed|s|ing)?|decrease(?:d|s|ing)?|fell|fallen|"
    r"drop(?:ped|s|ping)?|declin(?:e|ed|es|ing)|degrad(?:e|ed|es|ing)|"
    r"recover(?:ed|s|ing)?|restor(?:e|ed|es|ing)|returned?\s+to\s+baseline)\b"
    r"|(?:上升|增加|增长|激增|飙升|下降|降低|恶化|恢复)",
    re.IGNORECASE,
)
_BOUNDARY_SIGNAL = re.compile(
    r"\b(?:reach(?:ed|es|ing)?|hit|cross(?:ed|es|ing)?|exceed(?:ed|s|ing)?)\b"
    r".{0,64}\b(?:maximum|max|capacity|limit|quota|threshold|ceiling|full)\b"
    r"|\b(?:maximum|max|capacity|limit|quota|threshold|ceiling)\b.{0,64}"
    r"\b(?:reach(?:ed|es|ing)?|hit|full|zero)\b"
    r"|(?:达到|触及|超过).{0,32}(?:容量|上限|限额|阈值)",
    re.IGNORECASE,
)
_CAUSAL_SIGNAL = re.compile(
    r"\b(?:because|caused?\s+by|due\s+to|after|following|therefore|"
    r"result(?:ed|s)?\s+in|so\s+that|aligns?\s+with|correlat(?:ed|es)\s+with)\b"
    r"|(?:因为|导致|由于|之后|因此|相关)",
    re.IGNORECASE,
)
_ABNORMAL_STATE_SIGNAL = re.compile(
    r"\b(?:missing|blocked|killed|rejected|expired|stalled|malformed|unbounded|"
    r"inactive|nxdomain|out\s+of\s+space|no\s+(?:space|progress|available|idle))\b"
    r"|(?:缺失|阻塞|终止|拒绝|过期|停滞|畸形|无界|未启用|空间不足)",
    re.IGNORECASE,
)
_MULTIPLIER_SIGNAL = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*(?:x|×)(?!\w)", re.IGNORECASE)
_BENIGN_STATE_SIGNAL = re.compile(
    r"\b(?:completed(?:\s+successfully)?|succeeded|successful|healthy|passed|"
    r"without\s+errors?|remained\s+(?:stable|below)|stable|cache\s+warmed|"
    r"no\s+failures?|http\s+200|free\s+(?:disk\s+)?space|no\s+pressure)\b"
    r"|(?:成功完成|运行正常|保持稳定|无错误)",
    re.IGNORECASE,
)

_TASK_OVERLAP_WEIGHT = 1_500
_HARD_FAILURE_WEIGHT = 20_000
_CHANGE_WEIGHT = 6_000
_BOUNDARY_WEIGHT = 9_000
_CAUSAL_WEIGHT = 6_000
_ABNORMAL_STATE_WEIGHT = 7_500
_MULTIPLIER_WEIGHT = 4_000
_BENIGN_STATE_PENALTY = 17_500


class OpenVINORankingUnavailable(Exception):
    """Internal fixed failure for missing or unusable local inference."""

    def __init__(self) -> None:
        super().__init__("OPENVINO_RANKING_UNAVAILABLE")


class EmbeddingBackend(Protocol):
    """Small seam used by the ranker and its safety-boundary tests."""

    def embed_query(self, text: str) -> Sequence[float]: ...

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


@dataclass(frozen=True, slots=True)
class ModelManifest:
    model_id: str
    revision: str
    format: str
    installed_bytes: int
    files: Mapping[str, Mapping[str, Any]]
    fingerprint: str


@dataclass(frozen=True, slots=True)
class _SemanticCandidate:
    source: str
    start_line: int
    end_line: int
    text: str
    scope_anchor: str | None

    def fact(self, score: int) -> RankedFact:
        return RankedFact(
            source=self.source,
            start_line=self.start_line,
            end_line=self.end_line,
            text=self.text,
            score=score,
        )


@dataclass(frozen=True, slots=True)
class _HybridSignals:
    lexical_score: int
    task_overlap: int
    source_overlap: int
    hard_failure: bool
    change: bool
    boundary: bool
    causal: bool
    abnormal_state: bool
    multiplier: bool
    benign_state: bool

    @property
    def supported(self) -> bool:
        return bool(
            self.task_overlap
            or self.source_overlap
            or self.hard_failure
            or self.change
            or self.boundary
            or self.causal
            or self.abnormal_state
            or self.multiplier
        )

    @property
    def benign_only(self) -> bool:
        return self.benign_state and not self.supported


@dataclass(frozen=True, slots=True)
class _ScoredCandidate:
    final_score: int
    semantic_similarity: float
    semantic_score: int
    lane: str
    candidate: _SemanticCandidate
    vector: tuple[float, ...]
    signals: _HybridSignals
    scope_supported: bool | None


@dataclass(frozen=True, slots=True)
class _ScopeCalibration:
    affinities: Mapping[str, float]
    supported_anchors: frozenset[str]


def _repository_root() -> Path | None:
    """Find the source checkout or a project-local virtual environment owner."""

    try:
        for candidate in Path(__file__).resolve().parents:
            if (candidate / "pyproject.toml").is_file() and (
                candidate / "src" / "airlock"
            ).is_dir():
                return candidate
    except (OSError, RuntimeError):
        return None
    return None


def _user_cache_root() -> Path:
    configured = (
        os.environ.get("LOCALAPPDATA") if os.name == "nt" else os.environ.get("XDG_CACHE_HOME")
    )
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = Path.home() / candidate
        return candidate
    if os.name == "nt":
        return Path.home() / "AppData" / "Local"
    return Path.home() / ".cache"


def default_model_dir() -> Path:
    """Return a stable default that never depends on the process working directory."""

    repository = _repository_root()
    if repository is not None:
        return repository / DEFAULT_MODEL_SUBDIR
    return _user_cache_root() / "ai-airlock" / DEFAULT_MODEL_SUBDIR


def resolve_model_dir(model_dir: str | Path | None = None) -> Path:
    """Resolve explicit, environment, or default model paths without using cwd."""

    try:
        selected: str | Path
        if model_dir is not None:
            selected = model_dir
        elif os.environ.get(MODEL_DIR_ENV):
            selected = os.environ[MODEL_DIR_ENV]
        else:
            selected = default_model_dir()
        selected_path = Path(selected).expanduser()
        if not selected_path.is_absolute():
            selected_path = (_repository_root() or Path.home()) / selected_path
        return selected_path.resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError):
        raise OpenVINORankingUnavailable() from None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_model_dir(
    model_dir: str | Path | None = None,
    *,
    verify_hashes: bool = True,
) -> ModelManifest:
    """Validate a prepared model without exposing paths or parser errors."""

    root = resolve_model_dir(model_dir)
    manifest_path = root / MANIFEST_FILENAME
    try:
        if root.is_symlink() or not root.is_dir():
            raise ValueError
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise ValueError
        if manifest_path.stat().st_size > 64 * 1024:
            raise ValueError
        manifest_bytes = manifest_path.read_bytes()
        payload = json.loads(manifest_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        if payload.get("schema_version") != "0.1":
            raise ValueError
        if payload.get("model_id") != MODEL_ID or payload.get("revision") != MODEL_REVISION:
            raise ValueError
        if payload.get("format") != MODEL_FORMAT:
            raise ValueError
        installed_bytes = payload.get("installed_bytes")
        if (
            isinstance(installed_bytes, bool)
            or not isinstance(installed_bytes, int)
            or installed_bytes <= 0
            or installed_bytes > MODEL_SIZE_LIMIT_BYTES
        ):
            raise ValueError
        files = payload.get("files")
        if not isinstance(files, dict) or set(files) != _REQUIRED_MODEL_FILES:
            raise ValueError

        measured_total = manifest_path.stat().st_size
        for filename in sorted(_REQUIRED_MODEL_FILES):
            record = files.get(filename)
            artifact = root / filename
            if not isinstance(record, dict) or artifact.is_symlink() or not artifact.is_file():
                raise ValueError
            expected_bytes = record.get("bytes")
            expected_hash = record.get("sha256")
            if (
                isinstance(expected_bytes, bool)
                or not isinstance(expected_bytes, int)
                or expected_bytes <= 0
                or not isinstance(expected_hash, str)
                or len(expected_hash) != 64
            ):
                raise ValueError
            actual_bytes = artifact.stat().st_size
            if actual_bytes != expected_bytes:
                raise ValueError
            if verify_hashes and _sha256(artifact) != expected_hash:
                raise ValueError
            measured_total += actual_bytes
        if measured_total != installed_bytes:
            raise ValueError
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        raise OpenVINORankingUnavailable() from None

    return ModelManifest(
        model_id=MODEL_ID,
        revision=MODEL_REVISION,
        format=MODEL_FORMAT,
        installed_bytes=installed_bytes,
        files=files,
        fingerprint=hashlib.sha256(manifest_bytes).hexdigest(),
    )


def openvino_ready(model_dir: str | Path | None = None) -> bool:
    """Return true only when both the runtime and a complete local model exist."""

    try:
        root = resolve_model_dir(model_dir)
        manifest = validate_model_dir(root, verify_hashes=True)
        _load_runtime(str(root), manifest.fingerprint)
    except (ImportError, ModuleNotFoundError, OpenVINORankingUnavailable, ValueError):
        return False
    return True


@lru_cache(maxsize=2)
def _load_runtime(model_dir: str, manifest_fingerprint: str) -> tuple[Any, Any]:  # noqa: ARG001
    try:
        # Third-party advisory logs are not part of the public CLI contract.
        # Suppress them while preserving a fixed fail-closed exception.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            import openvino
            import openvino_genai

            tokenizer = openvino_genai.Tokenizer(
                model_dir,
                EXECUTION_MODE_HINT="ACCURACY",
            )
            core = openvino.Core()
            model = core.read_model(Path(model_dir) / "openvino_model.xml")
            compiled_model = core.compile_model(
                model,
                DEVICE,
                {"EXECUTION_MODE_HINT": "ACCURACY"},
            )
        return tokenizer, compiled_model
    except Exception:
        raise OpenVINORankingUnavailable() from None


def clear_openvino_runtime_cache() -> None:
    """Release cached native runtime handles before moving a prepared model."""

    _load_runtime.cache_clear()


class OpenVINOEmbeddingBackend:
    """OpenVINO tokenization and Runtime inference with deterministic pooling."""

    def __init__(self, model_dir: str | Path | None = None) -> None:
        root = resolve_model_dir(model_dir)
        manifest = validate_model_dir(root, verify_hashes=True)
        self._tokenizer, self._model = _load_runtime(str(root), manifest.fingerprint)

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        try:
            import numpy as np

            encoded = self._tokenizer.encode(list(texts))
            input_ids = np.asarray(encoded.input_ids.data, dtype=np.int64)
            attention_mask = np.asarray(encoded.attention_mask.data, dtype=np.int64)
            if input_ids.ndim != 2 or input_ids.shape[1] > MAX_INPUT_TOKENS:
                raise ValueError
            input_names = {item.any_name for item in self._model.inputs}
            inputs = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
            if "token_type_ids" in input_names:
                inputs["token_type_ids"] = np.zeros_like(input_ids)
            if set(inputs) != input_names:
                raise ValueError
            outputs = self._model(inputs)
            hidden_state = np.asarray(outputs[self._model.output("last_hidden_state")])
            attention_mask = attention_mask.astype(np.float32)
            if hidden_state.ndim != 3 or hidden_state.shape[:2] != attention_mask.shape:
                raise ValueError
            mask = attention_mask[..., None]
            pooled = (hidden_state.astype(np.float32) * mask).sum(axis=1)
            pooled /= np.maximum(mask.sum(axis=1), 1.0)
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            if not np.all(np.isfinite(norms)) or np.any(norms <= 0):
                raise ValueError
            normalized = pooled / norms
            return normalized.tolist()
        except Exception:
            raise OpenVINORankingUnavailable() from None

    def embed_query(self, text: str) -> Sequence[float]:
        return self._embed([QUERY_INSTRUCTION + text])[0]

    def document_token_count(self, text: str) -> int:
        """Count prefixed document tokens without allowing silent truncation."""

        try:
            encoded = self._tokenizer.encode([DOCUMENT_INSTRUCTION + text])
            shape = encoded.input_ids.data.shape
            if len(shape) != 2 or shape[0] != 1 or shape[1] <= 0:
                raise ValueError
            return int(shape[1])
        except Exception:
            raise OpenVINORankingUnavailable() from None

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        output: list[Sequence[float]] = []
        for offset in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = [
                DOCUMENT_INSTRUCTION + text
                for text in texts[offset : offset + EMBEDDING_BATCH_SIZE]
            ]
            output.extend(self._embed(batch))
        return output


def _utf8_fragments(text: str, max_bytes: int) -> tuple[str, ...]:
    if len(text.encode("utf-8")) <= max_bytes:
        return (text,)
    fragments: list[str] = []
    start = 0
    while start < len(text):
        end = start
        fragment_bytes = 0
        while end < len(text):
            width = len(text[end].encode("utf-8"))
            if end > start and fragment_bytes + width > max_bytes:
                break
            fragment_bytes += width
            end += 1
        fragments.append(text[start:end])
        if end >= len(text):
            break

        next_start = end
        overlap_bytes = 0
        overlap_limit = max(0, min(CHUNK_OVERLAP_UTF8_BYTES, max_bytes - 1))
        while next_start > start:
            width = len(text[next_start - 1].encode("utf-8"))
            if overlap_bytes + width > overlap_limit:
                break
            overlap_bytes += width
            next_start -= 1
        start = next_start
    return tuple(fragments)


def _token_safe_fragments(
    text: str,
    max_bytes: int,
    token_counter: Callable[[str], int] | None,
) -> tuple[str, ...]:
    fragments = list(_utf8_fragments(text, max_bytes))
    if token_counter is None:
        return tuple(fragments)

    safe: list[str] = []
    pending = list(reversed(fragments))
    while pending:
        fragment = pending.pop()
        if token_counter(fragment) <= MAX_DOCUMENT_TOKENS:
            safe.append(fragment)
            continue
        if len(fragment) <= 1:
            raise OpenVINORankingUnavailable()
        midpoint = len(fragment) // 2
        overlap = min(8, max(0, midpoint - 1), max(0, len(fragment) - midpoint - 1))
        left = fragment[: midpoint + overlap]
        right = fragment[midpoint - overlap :]
        if len(left) >= len(fragment) or len(right) >= len(fragment):
            raise OpenVINORankingUnavailable()
        pending.extend((right, left))
    return tuple(safe)


def _candidate_windows(
    documents: tuple[tuple[str, str], ...],
    *,
    token_counter: Callable[[str], int] | None = None,
) -> tuple[_SemanticCandidate, ...]:
    candidates: list[_SemanticCandidate] = []
    for source, text in documents:
        lines = text.splitlines()
        units: list[tuple[int, str, str | None]] = []
        for line_number, line in enumerate(lines, start=1):
            line_scope_anchor = _line_scope_anchor(line)
            for fragment in _token_safe_fragments(
                line,
                MAX_CHUNK_UTF8_BYTES,
                token_counter,
            ):
                units.append((line_number, fragment, line_scope_anchor))

        current: list[tuple[int, str, str | None]] = []
        current_bytes = 0
        current_lines: set[int] = set()
        current_scope_anchor: str | None = None

        def flush() -> None:
            nonlocal current, current_bytes, current_lines, current_scope_anchor
            if current:
                candidate_text = "\n".join(fragment for _, fragment, _ in current)
                visible = [
                    line.strip()
                    for line in candidate_text.splitlines()
                    if line.strip() and line.strip() != _ISOLATED_INSTRUCTION
                ]
                if visible:
                    candidates.append(
                        _SemanticCandidate(
                            source=source,
                            start_line=current[0][0],
                            end_line=current[-1][0],
                            text=candidate_text,
                            scope_anchor=current_scope_anchor,
                        )
                    )
            current = []
            current_bytes = 0
            current_lines = set()
            current_scope_anchor = None

        for line_number, fragment, fragment_scope_anchor in units:
            if not fragment.strip():
                flush()
                continue
            separator_bytes = 1 if current else 0
            fragment_bytes = len(fragment.encode("utf-8"))
            would_mix_scope = (
                current
                and line_number not in current_lines
                and current_scope_anchor is not None
                and fragment_scope_anchor is not None
                and fragment_scope_anchor != current_scope_anchor
            )
            would_exceed_lines = (
                line_number not in current_lines and len(current_lines) >= MAX_CHUNK_LINES
            )
            would_exceed_bytes = (
                current_bytes + separator_bytes + fragment_bytes > MAX_CHUNK_UTF8_BYTES
            )
            proposed_text = "\n".join([*(item[1] for item in current), fragment])
            would_exceed_tokens = (
                token_counter is not None and token_counter(proposed_text) > MAX_DOCUMENT_TOKENS
            )
            if current and (
                would_mix_scope or would_exceed_lines or would_exceed_bytes or would_exceed_tokens
            ):
                flush()
            current.append((line_number, fragment, fragment_scope_anchor))
            current_lines.add(line_number)
            current_bytes += (1 if len(current) > 1 else 0) + fragment_bytes
            if current_scope_anchor is None and fragment_scope_anchor is not None:
                current_scope_anchor = fragment_scope_anchor
        flush()

        if len(candidates) > MAX_CANDIDATE_WINDOWS:
            raise RankingError("CANDIDATE_LIMIT_EXCEEDED")

    return tuple(candidates)


def _unit_vector(values: Sequence[float]) -> tuple[float, ...]:
    try:
        vector = tuple(float(value) for value in values)
        if not vector or not all(math.isfinite(value) for value in vector):
            raise ValueError
        norm = math.sqrt(math.fsum(value * value for value in vector))
        if not math.isfinite(norm) or norm <= 0:
            raise ValueError
        return tuple(value / norm for value in vector)
    except (OverflowError, TypeError, ValueError):
        raise OpenVINORankingUnavailable() from None


def _quantized_similarity(left: Sequence[float], right: Sequence[float]) -> tuple[float, int]:
    left_unit = _unit_vector(left)
    right_unit = _unit_vector(right)
    if len(left_unit) != len(right_unit):
        raise OpenVINORankingUnavailable()
    similarity = max(-1.0, min(1.0, math.fsum(a * b for a, b in zip(left_unit, right_unit))))
    score = max(0, min(1_000_000, round((similarity + 1.0) * 500_000)))
    return similarity, score


def _task_is_diagnostic(task: str) -> bool:
    return bool(_DIAGNOSTIC_TASK.search(task))


def _source_tokens(source: str) -> frozenset[str]:
    """Tokenize path components without treating identifier separators as semantic glue."""

    return tokenize(_IDENTIFIER_SEPARATOR.sub(" ", source))


def _clean_log_token(token: str) -> str:
    return token.strip("[](){}<>,;:\"'")


def _line_scope_anchor(line: str) -> str | None:
    """Extract a generic structured-log producer without interpreting its product name."""

    field = _SCOPE_FIELD.search(line)
    if field is not None:
        return field.group(1).casefold()

    tokens = line.split()
    for index, raw_token in enumerate(tokens[:8]):
        token = _clean_log_token(raw_token)
        if token.upper() not in _LOG_LEVELS or index == 0:
            continue
        candidate = _clean_log_token(tokens[index - 1])
        if (
            _SCOPE_ANCHOR.fullmatch(candidate) is not None
            and not _TIMESTAMP_TOKEN.fullmatch(candidate)
            and candidate.upper() not in _LOG_LEVELS
        ):
            return candidate.casefold()
    return None


def _candidate_scope_anchor(candidate: _SemanticCandidate) -> str | None:
    return candidate.scope_anchor


def _producer_identity_tokens(anchor: str) -> frozenset[str]:
    """Return service-family tokens while excluding generic runtime roles."""

    return frozenset(
        token
        for token in tokenize(_IDENTIFIER_SEPARATOR.sub(" ", anchor))
        if len(token) >= 3
        and token not in _PRODUCER_ROLE_TOKENS
        and any(character.isalpha() for character in token)
    )


def _scope_anchors(candidates: Sequence[_SemanticCandidate]) -> tuple[str, ...]:
    anchors = tuple(
        sorted(
            {
                anchor
                for candidate in candidates
                if (anchor := _candidate_scope_anchor(candidate)) is not None
            }
        )
    )
    return anchors if len(anchors) >= MIN_SCOPE_ANCHORS else ()


def _scope_calibration(
    query_vector: Sequence[float],
    anchors: Sequence[str],
    vectors: Sequence[Sequence[float]],
) -> _ScopeCalibration | None:
    """Calibrate a high-confidence task-to-producer cluster for noisy log sets."""

    if len(anchors) < MIN_SCOPE_ANCHORS or len(vectors) != len(anchors):
        return None
    similarities = {
        anchor: _quantized_similarity(query_vector, vector)[0]
        for anchor, vector in zip(anchors, vectors)
    }
    values = tuple(similarities.values())
    top_similarity = max(values)
    center = median(values)
    if top_similarity < SCOPE_MIN_TOP_SIMILARITY or top_similarity - center < SCOPE_MIN_CONTRAST:
        return None

    target_floor = top_similarity - SCOPE_KEEP_MARGIN
    semantic_seeds = frozenset(
        anchor for anchor, similarity in similarities.items() if similarity >= target_floor
    )
    seed_identities = {anchor: _producer_identity_tokens(anchor) for anchor in semantic_seeds}
    supported_anchors = set(semantic_seeds)
    affinities: dict[str, float] = {
        anchor: max(0.0, similarities[anchor] - center) for anchor in semantic_seeds
    }
    for anchor in anchors:
        identity = _producer_identity_tokens(anchor)
        related_seeds = tuple(
            seed
            for seed, seed_identity in seed_identities.items()
            if identity and seed_identity and identity & seed_identity
        )
        if not related_seeds:
            continue
        supported_anchors.add(anchor)
        family_similarity = max(
            similarities[anchor],
            *(similarities[seed] for seed in related_seeds),
        )
        affinities[anchor] = max(0.0, family_similarity - center)

    return _ScopeCalibration(
        affinities=affinities,
        supported_anchors=frozenset(supported_anchors),
    )


def _hybrid_signals(
    task_tokens: frozenset[str],
    source: str,
    text: str,
) -> _HybridSignals:
    text_tokens = tokenize(text)
    return _HybridSignals(
        lexical_score=_line_score(text, task_tokens),
        task_overlap=len(text_tokens & task_tokens),
        source_overlap=len(_source_tokens(source) & task_tokens),
        hard_failure=_line_score(text, frozenset()) > 0,
        change=bool(_CHANGE_SIGNAL.search(text)),
        boundary=bool(_BOUNDARY_SIGNAL.search(text)),
        causal=bool(_CAUSAL_SIGNAL.search(text)),
        abnormal_state=bool(_ABNORMAL_STATE_SIGNAL.search(text)),
        multiplier=bool(_MULTIPLIER_SIGNAL.search(text)),
        benign_state=bool(_BENIGN_STATE_SIGNAL.search(text)),
    )


def _hybrid_score(
    semantic_score: int,
    signals: _HybridSignals,
    *,
    diagnostic_task: bool,
    scope_affinity: float | None = None,
) -> int:
    score = semantic_score + _TASK_OVERLAP_WEIGHT * min(signals.task_overlap, 6)
    score += _TASK_OVERLAP_WEIGHT * min(signals.source_overlap, 4)
    if scope_affinity is not None:
        score += round(SCOPE_AFFINITY_WEIGHT * scope_affinity)
    if diagnostic_task:
        score += _HARD_FAILURE_WEIGHT * signals.hard_failure
        score += _CHANGE_WEIGHT * signals.change
        score += _BOUNDARY_WEIGHT * signals.boundary
        score += _CAUSAL_WEIGHT * signals.causal
        score += _ABNORMAL_STATE_WEIGHT * signals.abnormal_state
        score += _MULTIPLIER_WEIGHT * signals.multiplier
        score -= _BENIGN_STATE_PENALTY * signals.benign_state
    return max(0, score)


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if len(left_tokens) < 3 or len(right_tokens) < 3:
        return 0.0
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union) if union else 0.0


def _near_duplicate(left: _ScoredCandidate, right: _ScoredCandidate) -> bool:
    similarity, _score = _quantized_similarity(left.vector, right.vector)
    return (
        similarity >= NEAR_DUPLICATE_SIMILARITY
        and _token_jaccard(
            left.candidate.text,
            right.candidate.text,
        )
        >= NEAR_DUPLICATE_TOKEN_JACCARD
    )


def rank_openvino_evidence(
    task: str,
    documents: Mapping[str, str],
    *,
    model_dir: str | Path | None = None,
    backend: EmbeddingBackend | None = None,
    max_facts: int = DEFAULT_MAX_FACTS,
    max_tokens: int = 4_000,
    reserved_tokens: int = 0,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> RankingResult:
    """Rank all sanitized text chunks with a local multilingual embedding model."""

    if (
        not isinstance(task, str)
        or isinstance(max_facts, bool)
        or not isinstance(max_facts, int)
        or max_facts <= 0
        or isinstance(max_tokens, bool)
        or not isinstance(max_tokens, int)
        or max_tokens <= 0
        or isinstance(reserved_tokens, bool)
        or not isinstance(reserved_tokens, int)
        or reserved_tokens < 0
        or reserved_tokens >= max_tokens
        or isinstance(min_similarity, bool)
        or not isinstance(min_similarity, (int, float))
        or not math.isfinite(float(min_similarity))
        or not -1.0 <= float(min_similarity) <= 1.0
    ):
        raise RankingError()

    normalized = _normalize_documents(documents)
    candidates = _candidate_windows(normalized)
    if not task.strip() or not candidates:
        return RankingResult(
            facts=(),
            status="NO_RELEVANT_CONTEXT",
            candidate_windows=len(candidates),
            selected_tokens_estimated=estimate_tokens("[]"),
        )

    selected_backend = backend if backend is not None else OpenVINOEmbeddingBackend(model_dir)
    diagnostic_task = _task_is_diagnostic(task)
    try:
        token_counter = getattr(selected_backend, "document_token_count", None)
        if not callable(token_counter):
            token_counter = None
        candidates = _candidate_windows(normalized, token_counter=token_counter)
        query_vector = selected_backend.embed_query(task)
        scope_anchors = _scope_anchors(candidates) if diagnostic_task else ()
        # Embed producer anchors and evidence in one document call.  Besides
        # preserving the E5 query/passage contract, this avoids a separate
        # short dynamic-shape inference after the full evidence batches.  That
        # shape transition can fault inside the OpenVINO CPU plugin on macOS.
        all_document_vectors = selected_backend.embed_documents(
            [*scope_anchors, *(candidate.text for candidate in candidates)]
        )
        if len(all_document_vectors) != len(scope_anchors) + len(candidates):
            raise OpenVINORankingUnavailable()
        anchor_count = len(scope_anchors)
        scope_calibration = (
            _scope_calibration(
                query_vector,
                scope_anchors,
                all_document_vectors[:anchor_count],
            )
            if scope_anchors
            else None
        )
        document_vectors = all_document_vectors[anchor_count:]
    except (OpenVINORankingUnavailable, RankingError):
        raise
    except Exception:
        raise OpenVINORankingUnavailable() from None
    task_tokens = tokenize(task)
    scored: list[_ScoredCandidate] = []
    for candidate, vector in zip(candidates, document_vectors):
        similarity, semantic_score = _quantized_similarity(query_vector, vector)
        signals = _hybrid_signals(task_tokens, candidate.source, candidate.text)
        anchor = _candidate_scope_anchor(candidate)
        scope_affinity = (
            scope_calibration.affinities.get(anchor)
            if scope_calibration is not None and anchor is not None
            else None
        )
        scope_supported = (
            None if scope_calibration is None else anchor in scope_calibration.supported_anchors
        )
        if diagnostic_task:
            if signals.benign_only:
                continue
            if signals.supported:
                if similarity < SUPPORTED_MIN_SIMILARITY:
                    continue
                lane = "supported"
            else:
                if similarity < float(min_similarity):
                    continue
                lane = "neutral"
        else:
            if similarity < float(min_similarity):
                continue
            lane = "semantic"
        scored.append(
            _ScoredCandidate(
                final_score=_hybrid_score(
                    semantic_score,
                    signals,
                    diagnostic_task=diagnostic_task,
                    scope_affinity=scope_affinity,
                ),
                semantic_similarity=similarity,
                semantic_score=semantic_score,
                lane=lane,
                candidate=candidate,
                vector=_unit_vector(vector),
                signals=signals,
                scope_supported=scope_supported,
            )
        )
    scored.sort(
        key=lambda item: (
            -item.final_score,
            -item.semantic_score,
            item.candidate.source,
            item.candidate.start_line,
        )
    )

    budget = max_tokens - reserved_tokens
    selected: list[RankedFact] = []
    selected_candidates: list[_ScoredCandidate] = []
    neutral_facts = 0
    out_of_scope_facts = 0
    selected_tokens = estimate_tokens("[]")
    for item in scored:
        if len(selected) >= max_facts:
            break
        if diagnostic_task and item.lane == "neutral" and neutral_facts >= MAX_NEUTRAL_FACTS:
            continue
        if (
            diagnostic_task
            and item.scope_supported is False
            and out_of_scope_facts >= MAX_OUT_OF_SCOPE_FACTS
        ):
            continue
        if any(_near_duplicate(item, existing) for existing in selected_candidates):
            continue
        proposed = [*selected, item.candidate.fact(item.final_score)]
        proposed_tokens = _facts_token_estimate(proposed)
        if proposed_tokens <= budget:
            selected = proposed
            selected_candidates.append(item)
            if item.lane == "neutral":
                neutral_facts += 1
            if item.scope_supported is False:
                out_of_scope_facts += 1
            selected_tokens = proposed_tokens

    if selected:
        status = "OK"
    elif scored:
        status = "TOKEN_BUDGET_EXHAUSTED"
    else:
        status = "NO_RELEVANT_CONTEXT"
    return RankingResult(
        facts=tuple(selected),
        status=status,
        candidate_windows=len(candidates),
        selected_tokens_estimated=selected_tokens,
    )


def openvino_inference_metadata(*, chunks_processed: int) -> dict[str, Any]:
    """Public metadata emitted only after the OpenVINO path succeeds."""

    return {
        "chunks_processed": chunks_processed,
        "device": DEVICE,
        "fallback_state": "not_used",
        "mode": INFERENCE_MODE,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "openvino_available": True,
    }
