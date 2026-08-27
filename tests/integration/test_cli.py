from __future__ import annotations

import json
from pathlib import Path

import pytest

from airlock import cli

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo" / "incident"


def test_json_cli_emits_one_document_and_no_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(
        [
            "analyze",
            "--task",
            "Analyze the payment failure",
            "--path",
            str(DEMO),
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert json.loads(captured.out)["decision"] == "ALLOW_WITH_TRANSFORM"


def test_human_cli_is_safe_and_useful(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main(
        [
            "analyze",
            "--task",
            "Analyze the payment failure",
            "--path",
            str(DEMO),
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "connection pool exhaustion" in captured.out
    assert "collector.invalid" not in captured.out
    assert "sk-test-" not in captured.out
    assert captured.err == ""


def test_invalid_arguments_never_echo_attacker_controlled_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    sentinel = "sk-test-ARGUMENTMUSTNOTLEAK"
    code = cli.main(["analyze", "--unknown", sentinel, "--json"])
    captured = capsys.readouterr()

    assert code == 1
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["error"]["code"] == "INVALID_ARGUMENTS"
    assert sentinel not in captured.err
    assert "Traceback" not in captured.err


def test_unexpected_exception_is_replaced_by_fixed_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sentinel = "sk-test-EXCEPTIONMUSTNOTLEAK"

    def fail(**_kwargs):
        raise RuntimeError(sentinel)

    monkeypatch.setattr(cli, "analyze", fail)
    code = cli.main(["analyze", "--task", "safe", "--path", str(DEMO), "--json"])
    captured = capsys.readouterr()

    assert code == 1
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "INTERNAL_ERROR"
    assert sentinel not in captured.err
    assert "Traceback" not in captured.err


def test_incomplete_input_returns_fixed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "sensitive-name.log").write_bytes(b"\xff\xfe")
    code = cli.main(["scan", "--path", str(tmp_path), "--json"])
    captured = capsys.readouterr()

    assert code == 1
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "INPUT_INCOMPLETE"
    assert "sensitive-name" not in captured.err


def test_audit_path_inside_input_is_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "safe.log").write_text("ERROR", encoding="utf-8")
    code = cli.main(
        [
            "scan",
            "--path",
            str(tmp_path),
            "--audit-log",
            str(tmp_path / "audit.jsonl"),
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "INPUT_INCOMPLETE"
