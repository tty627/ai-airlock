"""Execute a synthetic development example with scripted preset questions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from airlock.serialization import estimate_tokens, stable_json  # noqa: E402
from airlock.session import EvidenceSession  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("lexical", "openvino"), default="lexical")
    parser.add_argument("--model-dir")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    task = "Explain the export worker backlog increase and identify missing evidence."
    questions = [
        "What batch policy and concurrency values were recorded?",
        "What topology and arrival rate were observed?",
    ]
    started = perf_counter_ns()
    session = EvidenceSession.create(
        path=Path(__file__).resolve().parent / "incident",
        task=task,
        relevance_backend=args.backend,
        model_dir=args.model_dir,
    )
    responses = [session.initial()]
    for index, question in enumerate(questions, start=1):
        responses.append(
            session.query(session.case_id, session.version, question, f"scripted-{index}")
        )
    trace = {
        "kind": "synthetic_development_demo",
        "backend_requested": args.backend,
        "followup_policy": "scripted preset questions; no autonomous Agent or LLM is called",
        "scripted_preset_questions": questions,
        "task_correctness_measured": False,
        "elapsed_ms": round((perf_counter_ns() - started) / 1_000_000, 3),
        "full_responses_tokens_estimated": sum(
            estimate_tokens(stable_json(response)) for response in responses
        ),
        "responses": responses,
    }
    rendered = json.dumps(trace, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(stable_json({"output": str(args.output), "response_count": len(responses)}))
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
