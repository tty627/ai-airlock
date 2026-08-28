from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = PROJECT_ROOT / "scripts" / "run.ps1"


def test_wrapper_validates_the_production_form_before_bootstrap() -> None:
    source = WRAPPER.read_text(encoding="utf-8")

    assert source.index("$Command = if ($args.Count") < source.index(
        "$PackageStamp = Get-PackageStamp"
    )
    assert "[Console]::Out.Write($Invocation.Stdout)" not in source
    assert "AIRLOCK_ABSOLUTE_PATH_REQUIRED" in source
    assert "AIRLOCK_OPENVINO_REQUIRED" in source
    assert "AIRLOCK_OUTPUT_LIMIT_EXCEEDED" in source
    assert "$JsonRequested = $true" in source
    assert "$Component.StartsWith(' ', [StringComparison]::Ordinal)" in source
    assert "$Component.EndsWith(' ', [StringComparison]::Ordinal)" in source
    assert "$Component.EndsWith('.', [StringComparison]::Ordinal)" in source
    assert "StandardInput.WriteAsync" in source
    assert "$StdoutTask = $Process.StandardOutput.ReadToEndAsync()" not in source
    assert "$StderrTask = $Process.StandardError.ReadToEndAsync()" not in source


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


@pytest.mark.skipif(_powershell() is None, reason="PowerShell is unavailable")
@pytest.mark.parametrize(
    ("arguments", "expected_code", "json_error"),
    (
        (
            (
                "analyze",
                "--task",
                "diagnose",
                "--path",
                "relative/logs",
                "--relevance-backend",
                "openvino",
                "--json",
            ),
            "AIRLOCK_ABSOLUTE_PATH_REQUIRED",
            True,
        ),
        (
            (
                "analyze",
                "--task",
                "diagnose",
                "--path",
                "C:\\safe\\.. \\secret",
                "--relevance-backend",
                "openvino",
                "--json",
            ),
            "AIRLOCK_ABSOLUTE_PATH_REQUIRED",
            True,
        ),
        (
            (
                "analyze",
                "--task",
                "diagnose",
                "--path",
                "C:\\one",
                "--path",
                "C:\\two",
                "--relevance-backend",
                "openvino",
                "--json",
            ),
            "INVALID_ARGUMENTS",
            True,
        ),
        (
            (
                "analyze",
                "--task",
                "diagnose",
                "--path",
                "C:\\one",
                "--relevance-backend",
                "lexical",
                "--json",
            ),
            "AIRLOCK_OPENVINO_REQUIRED",
            True,
        ),
        (
            ("scan", "--path", "C:\\one", "--audit-log", "C:\\audit.jsonl", "--json"),
            "INVALID_ARGUMENTS",
            True,
        ),
        (("health",), "INVALID_ARGUMENTS", True),
    ),
)
def test_invalid_forms_fail_before_bootstrap(
    tmp_path: Path,
    arguments: tuple[str, ...],
    expected_code: str,
    json_error: bool,
) -> None:
    completed = subprocess.run(
        [
            _powershell(),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(WRAPPER),
            *arguments,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 1
    assert completed.stdout == ""
    if json_error:
        assert json.loads(completed.stderr)["error"]["code"] == expected_code
    else:
        assert completed.stderr.startswith(f"ERROR {expected_code}:")
