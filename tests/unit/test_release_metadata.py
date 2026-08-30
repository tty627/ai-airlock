from __future__ import annotations

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _frontmatter() -> dict[str, object]:
    source = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert source.startswith("---\n")
    _, raw, _ = source.split("---", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_skill_frontmatter_is_portable_to_modelscope_and_traecode() -> None:
    metadata = _frontmatter()

    assert metadata["name"] == "ai-airlock"
    assert metadata["metadata"] == {"version": "0.1.0"}
    assert isinstance(metadata["description"], str)
    assert len(metadata["description"]) <= 1024


def test_openvino_runtime_metadata_uses_documented_fields_and_budget() -> None:
    info = json.loads((PROJECT_ROOT / "info.json").read_text(encoding="utf-8"))

    assert set(info) == {
        "venv_name",
        "python_version",
        "mem_need_gb",
        "server_alive_timeout",
        "models",
    }
    assert info["python_version"] == "3.12"
    assert info["mem_need_gb"] >= 1.0
    assert info["server_alive_timeout"] == 300
    assert info["models"] == []


def test_store_metadata_uses_public_immutable_icon_and_confirmed_identity() -> None:
    meta = json.loads((PROJECT_ROOT / "meta.json").read_text(encoding="utf-8"))

    assert meta["name"] == "ai-airlock"
    assert meta["author"] == "谭天晔"
    assert meta["version"] == "0.1.0"
    assert meta["icon"] == (
        "https://raw.githubusercontent.com/tty627/ai-airlock/"
        "v0.1.0-rc.5/assets/competition/ai-airlock-icon.png"
    )


def test_traecode_acceptance_reference_is_routed_from_the_skill() -> None:
    skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "docs/trae-acceptance.md" in skill
    assert ".trae\\skills\\ai-airlock" in skill
    assert ".traecli\\skills\\ai-airlock" in skill
    assert "--continue" in skill
    assert "no cloud inference fallback" in skill.lower()


def test_release_builder_includes_submission_and_intel_evidence() -> None:
    builder = (PROJECT_ROOT / "scripts" / "build_release.ps1").read_text(encoding="utf-8")

    assert "'docs/modelscope-article-submission.md'" in builder
    assert "'docs/mac-submission-handoff.md'" in builder
    assert "'docs/windows-intel-rc6-evidence.md'" in builder
    assert "'docs/windows-intel-rc7-evidence.md'" in builder
