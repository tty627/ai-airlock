from __future__ import annotations

import weakref
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest

from airlock.relevance import model_setup, openvino_ranker


def _stub_model_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(model_setup.MODEL_CACHE_ENV, raising=False)
    monkeypatch.setattr(model_setup, "_download_sources", lambda _source, _cache: None)

    def convert(_source: Path, destination: Path) -> None:
        destination.mkdir()
        (destination / "runtime.lock").write_bytes(b"locked")

    monkeypatch.setattr(
        model_setup,
        "_convert_sources",
        convert,
    )
    monkeypatch.setattr(model_setup, "_write_manifest", lambda _candidate: {})
    monkeypatch.setattr(
        model_setup,
        "validate_model_dir",
        lambda _model_dir, *, verify_hashes: SimpleNamespace(installed_bytes=17),
    )


def _install_cached_smoke_backend(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fail: bool,
):
    handle_refs = []

    @lru_cache(maxsize=2)
    def load_runtime(model_dir: str, _fingerprint: str):
        handle = (Path(model_dir) / "runtime.lock").open("rb")
        handle_refs.append(weakref.ref(handle))
        return handle, object()

    class CachedSmokeBackend:
        def __init__(self, model_dir: Path) -> None:
            self._runtime = load_runtime(str(model_dir), "test-fingerprint")

        def embed_query(self, _text: str) -> list[float]:
            if fail:
                raise RuntimeError("private native failure")
            return [1.0, 0.0]

        def embed_documents(self, _texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0]]

    monkeypatch.setattr(openvino_ranker, "_load_runtime", load_runtime)
    monkeypatch.setattr(model_setup, "OpenVINOEmbeddingBackend", CachedSmokeBackend)
    return load_runtime, handle_refs


def _close_surviving_handles(load_runtime, handle_refs) -> None:
    load_runtime.cache_clear()
    for handle_ref in handle_refs:
        handle = handle_ref()
        if handle is not None:
            handle.close()


def test_prepare_model_releases_cached_runtime_when_smoke_test_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "prepared-model"

    _stub_model_files(monkeypatch)
    load_runtime, handle_refs = _install_cached_smoke_backend(monkeypatch, fail=True)

    try:
        with pytest.raises(model_setup.ModelSetupError) as captured:
            model_setup.prepare_model(output)

        assert captured.value.code == "MODEL_SMOKE_TEST_FAILED"
        assert captured.value.__context__ is None
        assert load_runtime.cache_info().currsize == 0
        assert not output.exists()
        assert not any(
            path.name.startswith(".airlock-model-") and path.name != ".airlock-model-download-cache"
            for path in tmp_path.iterdir()
        )
    finally:
        _close_surviving_handles(load_runtime, handle_refs)


def test_prepare_model_releases_smoke_runtime_before_atomic_promotion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "prepared-model"

    _stub_model_files(monkeypatch)
    load_runtime, handle_refs = _install_cached_smoke_backend(monkeypatch, fail=False)

    original_replace = Path.replace

    def windows_replace(candidate: Path, destination: Path) -> Path:
        assert load_runtime.cache_info().currsize == 0
        return original_replace(candidate, destination)

    monkeypatch.setattr(Path, "replace", windows_replace)

    try:
        result = model_setup.prepare_model(output)

        assert result["status"] == "ready"
        assert output.is_dir()
        assert (output / "runtime.lock").read_bytes() == b"locked"
        assert load_runtime.cache_info().currsize == 0
    finally:
        _close_surviving_handles(load_runtime, handle_refs)
