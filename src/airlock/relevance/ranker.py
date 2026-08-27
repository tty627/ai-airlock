"""Stable lexical evidence selection for the deterministic MVP.

This module does not infer or hard-code an incident root cause.  It selects
verbatim, already-sanitized evidence windows using task overlap and generic
operational-failure signals so a downstream agent can reason from provenance.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import ceil
from typing import Iterable, Mapping, Protocol, Sequence

from airlock.ingestion import IngestionResult, LoadedFile

TOKEN_ESTIMATOR = "utf8_bytes_div_4_ceil_v1"

_ASCII_WORD = re.compile(r"[a-z0-9]+(?:[_-][a-z0-9]+)*", re.IGNORECASE)
_CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_SEVERITY = re.compile(r"\b(?:ERROR|FATAL)\b")
_HTTP_5XX = re.compile(r"(?<!\d)5\d{2}(?!\d)")

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "this",
        "to",
        "why",
        "with",
    }
)

_ENGLISH_FAILURE_TERMS = frozenset(
    {
        "crash",
        "denied",
        "error",
        "exception",
        "exhausted",
        "exhaustion",
        "failed",
        "failure",
        "latency",
        "outage",
        "overflow",
        "retries",
        "retry",
        "saturated",
        "saturation",
        "storm",
        "timeout",
        "unavailable",
    }
)
_CHINESE_FAILURE_TERMS = (
    "不可用",
    "失败",
    "崩溃",
    "异常",
    "拒绝",
    "故障",
    "耗尽",
    "超时",
    "错误",
    "重试",
)


class RankingError(Exception):
    """Stable validation failure for ranker inputs."""

    def __init__(self, code: str = "INVALID_RANKING_INPUT") -> None:
        self.code = code
        super().__init__(code)


class _DocumentLike(Protocol):
    relative_path: str
    text: str


@dataclass(frozen=True, slots=True)
class RankedFact:
    source: str
    start_line: int
    end_line: int
    text: str
    score: int

    @property
    def relative_path(self) -> str:
        return self.source

    @property
    def local_ref(self) -> str:
        if self.start_line == self.end_line:
            return f"L{self.start_line}"
        return f"L{self.start_line}-L{self.end_line}"

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class RankingResult:
    facts: tuple[RankedFact, ...]
    status: str
    candidate_windows: int
    selected_tokens_estimated: int
    token_estimator: str = TOKEN_ESTIMATOR


@dataclass(frozen=True, slots=True)
class _Candidate:
    source: str
    start: int
    end: int
    text: str
    score: int

    def fact(self) -> RankedFact:
        return RankedFact(
            source=self.source,
            start_line=self.start + 1,
            end_line=self.end + 1,
            text=self.text,
            score=self.score,
        )


def estimate_tokens(value: str | bytes) -> int:
    """Estimate tokens as ``ceil(len(UTF-8 bytes) / 4)``."""

    payload = value.encode("utf-8") if isinstance(value, str) else value
    return ceil(len(payload) / 4)


def tokenize(text: str) -> frozenset[str]:
    """Lowercase ASCII words plus bigrams from contiguous CJK runs."""

    if not isinstance(text, str):
        raise RankingError()
    tokens = {
        token.lower() for token in _ASCII_WORD.findall(text) if token.lower() not in _STOPWORDS
    }
    for match in _CJK_RUN.finditer(text):
        run = match.group(0)
        if len(run) == 1:
            tokens.add(run)
        else:
            tokens.update(run[index : index + 2] for index in range(len(run) - 1))
    return frozenset(tokens)


def _line_score(line: str, task_tokens: frozenset[str]) -> int:
    line_tokens = tokenize(line)
    overlap = len(line_tokens & task_tokens)
    score = overlap * 4
    score += len(line_tokens & _ENGLISH_FAILURE_TERMS) * 3
    lowered = line.lower()
    score += sum(3 for term in _CHINESE_FAILURE_TERMS if term in lowered)
    score += len(_SEVERITY.findall(line)) * 5
    score += len(_HTTP_5XX.findall(line)) * 4
    return score


def _normalize_documents(
    documents: IngestionResult | Mapping[str, str] | Sequence[LoadedFile] | Iterable[_DocumentLike],
) -> tuple[tuple[str, str], ...]:
    if isinstance(documents, IngestionResult):
        pairs = [(item.relative_path, item.text) for item in documents.files]
    elif isinstance(documents, Mapping):
        pairs = list(documents.items())
    else:
        if isinstance(documents, (str, bytes)):
            raise RankingError()
        try:
            pairs = [(item.relative_path, item.text) for item in documents]
        except (AttributeError, TypeError):
            raise RankingError() from None

    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for source, text in pairs:
        if (
            not isinstance(source, str)
            or not source
            or source.startswith("/")
            or "\\" in source
            or not isinstance(text, str)
            or source in seen
        ):
            raise RankingError()
        components = source.split("/")
        if any(component in {"", ".", ".."} for component in components):
            raise RankingError()
        seen.add(source)
        normalized.append((source, text))
    normalized.sort(key=lambda item: item[0])
    return tuple(normalized)


def _candidates(task: str, documents: tuple[tuple[str, str], ...]) -> list[_Candidate]:
    task_tokens = tokenize(task)
    output: list[_Candidate] = []
    for source, text in documents:
        lines = text.splitlines()
        scored = {
            index: _line_score(line, task_tokens)
            for index, line in enumerate(lines)
            if line.strip()
        }
        positive = {index: score for index, score in scored.items() if score > 0}
        if not positive:
            continue

        windows = [
            (max(0, index - 2), min(len(lines) - 1, index + 2), {index}) for index in positive
        ]
        merged: list[tuple[int, int, set[int]]] = []
        for start, end, seeds in windows:
            if merged and start <= merged[-1][1]:
                previous_start, previous_end, previous_seeds = merged[-1]
                merged[-1] = (
                    previous_start,
                    max(previous_end, end),
                    previous_seeds | seeds,
                )
            else:
                merged.append((start, end, seeds))

        for start, end, seeds in merged:
            output.append(
                _Candidate(
                    source=source,
                    start=start,
                    end=end,
                    text="\n".join(lines[start : end + 1]),
                    score=sum(positive[index] for index in seeds),
                )
            )

    output.sort(key=lambda candidate: (-candidate.score, candidate.source, candidate.start))
    return output


def _facts_token_estimate(facts: list[RankedFact]) -> int:
    serialized = json.dumps(
        [fact.as_dict() for fact in facts],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return estimate_tokens(serialized)


def rank_evidence(
    task: str,
    documents: IngestionResult | Mapping[str, str] | Sequence[LoadedFile] | Iterable[_DocumentLike],
    *,
    max_facts: int | None = None,
    max_tokens: int = 4000,
    reserved_tokens: int = 0,
) -> RankingResult:
    """Select stable ``line +/- 2`` evidence windows within a token budget.

    Inputs must already have prompt-injection spans isolated and sensitive
    spans transformed.  The output is ordered by descending score, then source
    and 1-based line number.
    """

    if not isinstance(task, str):
        raise RankingError()
    if (
        isinstance(max_tokens, bool)
        or not isinstance(max_tokens, int)
        or max_tokens <= 0
        or isinstance(reserved_tokens, bool)
        or not isinstance(reserved_tokens, int)
        or reserved_tokens < 0
        or reserved_tokens >= max_tokens
        or (
            max_facts is not None
            and (isinstance(max_facts, bool) or not isinstance(max_facts, int) or max_facts <= 0)
        )
    ):
        raise RankingError()

    normalized = _normalize_documents(documents)
    candidates = _candidates(task, normalized)
    if not candidates:
        return RankingResult(
            facts=(),
            status="NO_RELEVANT_CONTEXT",
            candidate_windows=0,
            selected_tokens_estimated=estimate_tokens("[]"),
        )

    budget = max_tokens - reserved_tokens
    selected: list[RankedFact] = []
    selected_tokens = estimate_tokens("[]")
    for candidate in candidates:
        if max_facts is not None and len(selected) >= max_facts:
            break
        proposed = [*selected, candidate.fact()]
        proposed_tokens = _facts_token_estimate(proposed)
        if proposed_tokens <= budget:
            selected = proposed
            selected_tokens = proposed_tokens

    status = "OK" if selected else "TOKEN_BUDGET_EXHAUSTED"
    return RankingResult(
        facts=tuple(selected),
        status=status,
        candidate_windows=len(candidates),
        selected_tokens_estimated=selected_tokens,
    )
