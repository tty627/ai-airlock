from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "benchmark" / "run_benchmark.py"


def test_blackbox_smoke_enforces_flagship_and_secret_gates(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--smoke", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["status"] == "PASS"

    report = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    provenance = report["provenance"]
    assert provenance["run_id"]
    assert provenance["python_version"]
    assert provenance["inputs_sha256"]["benchmark/run_benchmark.py"]
    assert provenance["inputs_sha256"]["benchmark/variants.json"]
    rules = report["variants"]["rules-only"]
    assert rules["status"] == "PASS"
    assert all(rules["acceptance_gates"].values())
    assert rules["flagship"]["status"] == "PASS"
    assert rules["flagship"]["forbidden_values_tested"] >= 248
    assert rules["security"]["secret_detection"]["status"] == "PASS"
    assert rules["security"]["secret_leakage_count"] == 0
    assert rules["security"]["prompt_injection"]["quality_gate"]["pass"] is True
    assert rules["utility"]["required_facts_retained"] == 3
    assert rules["utility"]["required_facts_total"] == 3
    assert rules["context"]["measurement_source"] == "benchmark_computed_from_cli_io"
    assert rules["context"]["cli_reported_metrics_match"] is True


def test_generated_benchmark_reports_do_not_contain_secret_sentinels(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--smoke", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    public = completed.stdout + (tmp_path / "latest.json").read_text(encoding="utf-8")
    public += (tmp_path / "latest.md").read_text(encoding="utf-8")
    assert "MY_SUPER_SECRET_982374" not in public
    assert "DO_NOT_LEAK_ME_445566" not in public
    assert "sk-test-MY" not in public
    assert "INTEGRATOR_SECRET_X91Q7" not in public
    assert "INTEGRATOR_PASSWORD_4AB92" not in public


def test_benchmark_datasets_have_balanced_stable_labels() -> None:
    datasets = ROOT / "benchmark" / "datasets"
    injection = json.loads((datasets / "injection_cases.json").read_text(encoding="utf-8"))
    relevance = json.loads((datasets / "relevance_cases.json").read_text(encoding="utf-8"))

    malicious = [case for case in injection["cases"] if case["label"] == "malicious"]
    benign = [case for case in injection["cases"] if case["label"] == "benign"]
    assert len(malicious) >= 2
    assert len(benign) >= 2

    ids: set[str] = set()
    assert 10 <= len(relevance["tasks"]) <= 20
    for task in relevance["tasks"]:
        relevant = [chunk for chunk in task["chunks"] if chunk["label"] == "relevant"]
        irrelevant = [chunk for chunk in task["chunks"] if chunk["label"] == "irrelevant"]
        assert 3 <= len(relevant) <= 5
        assert 5 <= len(irrelevant) <= 10
        for chunk in task["chunks"]:
            assert chunk["id"] not in ids
            assert chunk["source"] == f"{chunk['id']}.txt"
            ids.add(chunk["id"])
