from __future__ import annotations

import re
from pathlib import Path

import pytest

from airlock.capsule.leak_guard import enforce_public_payload_is_safe
from airlock.capsule.pseudonymizer import ConsistentPseudonymizer
from airlock.capsule.redactor import transform_text
from airlock.detectors import detect_all, detect_pii
from airlock.pipeline import analyze
from airlock.serialization import stable_json


def _email_values(text: str) -> list[str]:
    return [
        text[finding.span.start : finding.span.end]
        for finding in detect_pii(text)
        if finding.type == "EMAIL"
    ]


@pytest.mark.parametrize("field", ["owner", "Contact", "EMAIL", "email_address", "emailAddress"])
@pytest.mark.parametrize("separator", ["=", " =", "= ", " = "])
def test_email_field_name_is_preserved_and_only_value_is_sensitive(field, separator) -> None:
    value = "person-a@example.invalid"
    text = f"Account record {field}{separator}{value}."
    assert _email_values(text) == [value]

    result = transform_text(text, detect_all(text))

    assert result.text == f"Account record {field}{separator}[EMAIL_001]."
    assert set(result.sensitive_values) == {value}
    enforce_public_payload_is_safe(result.text, result.sensitive_values)


def test_different_fields_share_one_identity_across_files_and_keep_distinct_people() -> None:
    engine = ConsistentPseudonymizer()
    accounts = (
        "Account acct42 owner=person-a@example.invalid. "
        "Account acct99 owner=person-b@example.invalid.\n"
    )
    complaint = "Support complaint: repeated login prompt. Contact=person-a@example.invalid.\n"

    account_result = transform_text(accounts, detect_all(accounts, "accounts.txt"), engine)
    complaint_result = transform_text(complaint, detect_all(complaint, "complaint.txt"), engine)

    assert account_result.text == (
        "Account acct42 owner=[EMAIL_001]. Account acct99 owner=[EMAIL_002].\n"
    )
    assert complaint_result.text == (
        "Support complaint: repeated login prompt. Contact=[EMAIL_001].\n"
    )
    assert len(engine) == 2
    enforce_public_payload_is_safe(
        [account_result.text, complaint_result.text],
        [*account_result.sensitive_values, *complaint_result.sensitive_values],
    )


@pytest.mark.parametrize(
    "address",
    [
        "person+support@example.invalid",
        "first=last@example.invalid",
        "person+tag=value@example.invalid",
        "person=tag=value@example.invalid",
        "owner+tag=value@example.invalid",
        "team=person@example.invalid",
        "=person@example.invalid",
    ],
)
def test_legal_plus_and_equals_local_parts_remain_whole_and_distinct(address) -> None:
    text = f"Contact address: {address}."
    assert _email_values(text) == [address]
    result = transform_text(text, detect_all(text))
    assert result.text == "Contact address: [EMAIL_001]."
    assert set(result.sensitive_values) == {address}


@pytest.mark.parametrize("wrapper", ["<{}>", '"{}"', "mailto:{}"])
def test_explicit_address_context_preserves_a_local_part_that_looks_like_a_field(wrapper) -> None:
    address = "owner=person@example.invalid"
    text = wrapper.format(address)
    assert _email_values(text) == [address]
    result = transform_text(text, detect_all(text))
    assert result.text == wrapper.format("[EMAIL_001]")


@pytest.mark.parametrize(
    "value",
    [
        "person+tag=value@example.invalid",
        "first=last@example.invalid",
        "owner=person@example.invalid",
    ],
)
@pytest.mark.parametrize("quotes", ["", "'", '"'])
def test_assignment_preserves_equals_inside_value_and_quote_delimiters(value, quotes) -> None:
    text = f"Contact={quotes}{value}{quotes}"
    assert _email_values(text) == [value]
    result = transform_text(text, detect_all(text))
    assert result.text == f"Contact={quotes}[EMAIL_001]{quotes}"
    assert set(result.sensitive_values) == {value}


def test_mixed_addresses_keep_order_exact_spans_and_original_line_numbers() -> None:
    text = (
        "first=last@example.invalid\n"
        "{owner=person-a@example.invalid,Contact=person-b@example.invalid}\n"
        "mailbox=team@example.invalid\n"
    )
    findings = [finding for finding in detect_pii(text) if finding.type == "EMAIL"]
    assert [text[item.span.start : item.span.end] for item in findings] == [
        "first=last@example.invalid",
        "person-a@example.invalid",
        "person-b@example.invalid",
        "mailbox=team@example.invalid",
    ]
    assert [item.line for item in findings] == [1, 2, 2, 3]


def test_missing_value_does_not_strip_prefix_from_another_address() -> None:
    text = "owner=\nfirst=last@example.invalid"
    assert _email_values(text) == ["first=last@example.invalid"]


def test_pipeline_retains_joinable_customer_identity_and_field_labels(tmp_path: Path) -> None:
    (tmp_path / "accounts.txt").write_text(
        "Account acct42 owner=person-a@example.invalid. "
        "Account acct99 owner=person-b@example.invalid.\n",
        encoding="utf-8",
    )
    (tmp_path / "complaint.txt").write_text(
        "Support complaint: repeated login prompt. Contact=person-a@example.invalid.\n",
        encoding="utf-8",
    )
    capsule = analyze(task="Trace the account associated with the support complaint", path=tmp_path)
    facts = "\n".join(fact["text"] for fact in capsule["safe_context"]["facts"])
    account_a = re.search(r"Account acct42 owner=(\[EMAIL_\d+\])", facts)
    account_b = re.search(r"Account acct99 owner=(\[EMAIL_\d+\])", facts)
    contact = re.search(r"Contact=(\[EMAIL_\d+\])", facts)

    assert account_a and account_b and contact
    assert account_a[1] == contact[1] != account_b[1]
    public = stable_json(capsule)
    assert "person-a@example.invalid" not in public
    assert "person-b@example.invalid" not in public
