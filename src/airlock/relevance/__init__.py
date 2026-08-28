"""Safe task relevance and evidence-window selection."""

from .openvino_ranker import (
    DEFAULT_MODEL_SUBDIR,
    INFERENCE_MODE,
    MODEL_ID,
    MODEL_REVISION,
    SELECTION_METHOD,
    OpenVINORankingUnavailable,
    default_model_dir,
    openvino_inference_metadata,
    openvino_ready,
    rank_openvino_evidence,
)
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
    "DEFAULT_MODEL_SUBDIR",
    "INFERENCE_MODE",
    "MODEL_ID",
    "MODEL_REVISION",
    "SELECTION_METHOD",
    "OpenVINORankingUnavailable",
    "RankedFact",
    "RankingError",
    "RankingResult",
    "default_model_dir",
    "estimate_tokens",
    "openvino_inference_metadata",
    "openvino_ready",
    "rank_evidence",
    "rank_openvino_evidence",
    "tokenize",
]
