from __future__ import annotations

import json

import pytest

from airlock.relevance import RankingError, estimate_tokens, rank_evidence, tokenize


def test_task_overlap_and_failure_signals_select_line_plus_minus_two() -> None:
    documents = {
        "service.log": "\n".join(
            [
                "startup complete",
                "worker ready",
                "request accepted",
                "ERROR payment failed with status 503",
                "retry scheduled",
                "queue depth rising",
                "unrelated tail",
            ]
        )
    }

    result = rank_evidence("analyze payment failure", documents)

    assert result.status == "OK"
    assert len(result.facts) == 1
    fact = result.facts[0]
    # The adjacent retry signal contributes its own +/-2 window, so the two
    # overlapping windows merge through line 7.
    assert fact.local_ref == "L2-L7"
    assert "payment failed" in fact.text
    assert "startup complete" not in fact.text
    assert fact.score > 0


def test_overlapping_seed_windows_are_merged_without_duplicate_text() -> None:
    result = rank_evidence(
        "worker failure",
        {"a.log": "zero\none\nworker failed\nthree\nretry storm\nfive\nsix"},
    )

    assert len(result.facts) == 1
    assert result.facts[0].local_ref == "L1-L7"
    assert result.facts[0].text.count("worker failed") == 1


def test_stable_sorting_is_independent_of_mapping_insertion_order() -> None:
    first = {"z.log": "ERROR one", "a.log": "ERROR two"}
    second = {"a.log": "ERROR two", "z.log": "ERROR one"}

    output_a = rank_evidence("", first)
    output_b = rank_evidence("", second)

    assert output_a == output_b
    assert [fact.source for fact in output_a.facts] == ["a.log", "z.log"]


def test_no_positive_signal_returns_explicit_empty_status() -> None:
    result = rank_evidence("payment", {"notes.md": "gardening notes\nblue sky"})

    assert result.facts == ()
    assert result.status == "NO_RELEVANT_CONTEXT"
    assert result.candidate_windows == 0


def test_ascii_words_and_cjk_bigrams_drive_task_relevance() -> None:
    assert {"redis", "连接", "接池"}.issubset(tokenize("Redis 连接池"))

    result = rank_evidence("排查连接池", {"ops.log": "服务连接池达到上限"})

    assert result.status == "OK"
    assert result.facts[0].score >= 4


def test_generic_chinese_and_english_failure_signals_work_without_task_overlap() -> None:
    result = rank_evidence(
        "",
        {
            "a.log": "请求超时并触发重试",
            "b.log": "FATAL upstream unavailable with HTTP 502",
        },
    )

    assert result.status == "OK"
    assert {fact.source for fact in result.facts} == {"a.log", "b.log"}


def test_budget_and_max_facts_are_enforced_using_declared_estimator() -> None:
    documents = {
        "a.log": "ERROR " + "x" * 200,
        "b.log": "ERROR short",
        "c.log": "FATAL short",
    }

    result = rank_evidence("", documents, max_facts=1, max_tokens=60)

    assert len(result.facts) == 1
    assert result.facts[0].source in {"b.log", "c.log"}
    assert result.selected_tokens_estimated <= 60
    serialized = json.dumps(
        [fact.as_dict() for fact in result.facts],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert result.selected_tokens_estimated == estimate_tokens(serialized)
    assert result.token_estimator == "utf8_bytes_div_4_ceil_v1"


def test_positive_evidence_that_cannot_fit_has_distinct_status() -> None:
    result = rank_evidence("", {"a.log": "ERROR " + "x" * 100}, max_tokens=1)

    assert result.facts == ()
    assert result.status == "TOKEN_BUDGET_EXHAUSTED"


@pytest.mark.parametrize(
    ("task", "documents", "kwargs"),
    [
        (None, {}, {}),
        ("task", {"../escape.log": "ERROR"}, {}),
        ("task", {"a\\b.log": "ERROR"}, {}),
        ("task", {}, {"max_tokens": 0}),
        ("task", {}, {"max_facts": True}),
    ],
)
def test_invalid_ranker_inputs_have_fixed_error(task, documents, kwargs) -> None:
    with pytest.raises(RankingError, match="^INVALID_RANKING_INPUT$"):
        rank_evidence(task, documents, **kwargs)
