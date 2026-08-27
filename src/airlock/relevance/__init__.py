"""Deterministic task relevance and evidence-window selection."""

from .ranker import (
    TOKEN_ESTIMATOR,
    RankedFact,
    RankingError,
    RankingResult,
    estimate_tokens,
    rank_evidence,
    tokenize,
)

__all__ = [
    "TOKEN_ESTIMATOR",
    "RankedFact",
    "RankingError",
    "RankingResult",
    "estimate_tokens",
    "rank_evidence",
    "tokenize",
]
