"""Download and atomically prepare the pinned OpenVINO embedding model."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, NoReturn

from airlock.relevance.openvino_ranker import (
    DEFAULT_MODEL_SUBDIR,
    MANIFEST_FILENAME,
    MODEL_CACHE_ENV,
    MODEL_FORMAT,
    MODEL_ID,
    MODEL_REVISION,
    MODEL_SIZE_LIMIT_BYTES,
    OpenVINOEmbeddingBackend,
    OpenVINORankingUnavailable,
    resolve_model_dir,
    validate_model_dir,
)
from airlock.serialization import stable_json

_SOURCE_ARTIFACTS = (
    (
        "config.json",
        "config.json",
        655,
        "69137736cab8b8903a07fe8afaafdda25aac55415a12a55d1bffa9f581abf959",
    ),
    (
        "openvino/openvino_model.bin",
        "openvino_model.bin",
        470_027_936,
        "22f5a10ec005a1606ec42758dedd52b59dfcb6e3d85de0b6b86946d0bc6cf232",
    ),
    (
        "openvino/openvino_model.xml",
        "openvino_model.xml",
        363_385,
        "d5268b47f8d05ca885ffbc77f136c3406ac6acdf85c482caec66eebab7fa5176",
    ),
    (
        "special_tokens_map.json",
        "special_tokens_map.json",
        167,
        "d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7",
    ),
    (
        "tokenizer.json",
        "tokenizer.json",
        17_082_730,
        "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39",
    ),
    (
        "tokenizer_config.json",
        "tokenizer_config.json",
        443,
        "a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b",
    ),
)
_SOURCE_MODEL_BYTES = 470_027_936
_SOURCE_MODEL_SHA256 = "22f5a10ec005a1606ec42758dedd52b59dfcb6e3d85de0b6b86946d0bc6cf232"
_FINAL_FILES = (
    "config.json",
    "openvino_model.bin",
    "openvino_model.xml",
    "openvino_tokenizer.bin",
    "openvino_tokenizer.xml",
    "special_tokens_map.json",
    "tokenizer_config.json",
)


class ModelSetupError(Exception):
    """Fixed model setup failure without remote or local exception text."""

    def __init__(self, code: str = "MODEL_SETUP_FAILED") -> None:
        self.code = code
        super().__init__(code)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _download_sources(destination: Path, cache_dir: Path) -> None:
    try:
        from huggingface_hub import hf_hub_download

        for remote_name, local_name, _expected_bytes, _expected_hash in _SOURCE_ARTIFACTS:
            cached = Path(
                hf_hub_download(
                    repo_id=MODEL_ID,
                    filename=remote_name,
                    revision=MODEL_REVISION,
                    cache_dir=cache_dir,
                )
            )
            shutil.copyfile(cached, destination / local_name)
    except Exception:
        raise ModelSetupError("MODEL_DOWNLOAD_FAILED") from None

    try:
        for _remote_name, local_name, expected_bytes, expected_hash in _SOURCE_ARTIFACTS:
            artifact = destination / local_name
            if artifact.stat().st_size != expected_bytes or _sha256(artifact) != expected_hash:
                raise ModelSetupError("MODEL_SOURCE_MISMATCH")
    except OSError:
        raise ModelSetupError("MODEL_SOURCE_MISMATCH") from None


def _convert_sources(source: Path, destination: Path) -> None:
    try:
        # Conversion libraries may print optional-framework notices. Keep the
        # setup command machine-readable and replace failures with fixed codes.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            import openvino
            from openvino_tokenizers import convert_tokenizer
            from transformers import AutoTokenizer

            destination.mkdir()
            core = openvino.Core()
            model = core.read_model(
                source / "openvino_model.xml",
                source / "openvino_model.bin",
            )
            openvino.save_model(
                model,
                destination / "openvino_model.xml",
                compress_to_fp16=True,
            )

            tokenizer = AutoTokenizer.from_pretrained(
                source,
                local_files_only=True,
                trust_remote_code=False,
                use_fast=True,
            )
            openvino_tokenizer = convert_tokenizer(tokenizer)
            openvino.save_model(
                openvino_tokenizer,
                destination / "openvino_tokenizer.xml",
                compress_to_fp16=False,
            )

            for filename in (
                "config.json",
                "special_tokens_map.json",
                "tokenizer_config.json",
            ):
                shutil.copyfile(source / filename, destination / filename)
    except ModelSetupError:
        raise
    except Exception:
        raise ModelSetupError("MODEL_CONVERSION_FAILED") from None


def _verify_inference(model_dir: Path) -> None:
    try:
        backend = OpenVINOEmbeddingBackend(model_dir)
        query = backend.embed_query("本地支付故障")
        documents = backend.embed_documents(["payment service incident"])
        if not query or len(documents) != 1 or len(query) != len(documents[0]):
            raise ValueError
    except Exception:
        raise ModelSetupError("MODEL_SMOKE_TEST_FAILED") from None


def _write_manifest(model_dir: Path) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    try:
        for filename in _FINAL_FILES:
            path = model_dir / filename
            files[filename] = {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
    except OSError:
        raise ModelSetupError("MODEL_CONVERSION_FAILED") from None

    manifest: dict[str, Any] = {
        "schema_version": "0.1",
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "format": MODEL_FORMAT,
        "source_model": {
            "bytes": _SOURCE_MODEL_BYTES,
            "sha256": _SOURCE_MODEL_SHA256,
        },
        "source_artifacts": {
            local_name: {"bytes": expected_bytes, "sha256": expected_hash}
            for _remote_name, local_name, expected_bytes, expected_hash in _SOURCE_ARTIFACTS
        },
        "files": files,
        "installed_bytes": 0,
    }
    manifest_path = model_dir / MANIFEST_FILENAME
    for _ in range(8):
        manifest_path.write_text(stable_json(manifest) + "\n", encoding="utf-8", newline="\n")
        measured = manifest_path.stat().st_size + sum(record["bytes"] for record in files.values())
        if measured == manifest["installed_bytes"]:
            break
        manifest["installed_bytes"] = measured
    else:
        raise ModelSetupError("MODEL_MANIFEST_FAILED")

    if manifest["installed_bytes"] > MODEL_SIZE_LIMIT_BYTES:
        raise ModelSetupError("MODEL_SIZE_LIMIT_EXCEEDED")
    return manifest


def prepare_model(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Prepare a verified model directory without overwriting existing data."""

    try:
        output = resolve_model_dir(output_dir)
        parent = output.parent
        parent.mkdir(parents=True, exist_ok=True)
    except OpenVINORankingUnavailable:
        raise ModelSetupError("INVALID_MODEL_OUTPUT") from None
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ModelSetupError("INVALID_MODEL_OUTPUT") from None

    if output.exists() or output.is_symlink():
        try:
            manifest = validate_model_dir(output, verify_hashes=True)
        except Exception:
            raise ModelSetupError("MODEL_OUTPUT_EXISTS") from None
        return {
            "artifact_bytes": manifest.installed_bytes,
            "limit_bytes": MODEL_SIZE_LIMIT_BYTES,
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "status": "already_ready",
        }

    configured_cache = os.environ.get(MODEL_CACHE_ENV)
    try:
        download_cache = (
            Path(configured_cache).expanduser().resolve(strict=False)
            if configured_cache
            else parent / ".airlock-model-download-cache"
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ModelSetupError("MODEL_CACHE_INVALID") from None
    owns_cache = configured_cache is None
    try:
        if download_cache.is_symlink() or (download_cache.exists() and not download_cache.is_dir()):
            raise ModelSetupError("MODEL_CACHE_INVALID")
        download_cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".airlock-model-", dir=parent) as temporary:
            workspace = Path(temporary)
            source = workspace / "source"
            candidate = workspace / "candidate"
            source.mkdir()
            _download_sources(source, download_cache)
            _convert_sources(source, candidate)
            _write_manifest(candidate)
            _verify_inference(candidate)
            candidate.replace(output)
    except ModelSetupError:
        raise
    except Exception:
        raise ModelSetupError() from None

    try:
        validated = validate_model_dir(output, verify_hashes=True)
    except Exception:
        raise ModelSetupError("MODEL_FINAL_VALIDATION_FAILED") from None
    if owns_cache:
        shutil.rmtree(download_cache, ignore_errors=True)
    return {
        "artifact_bytes": validated.installed_bytes,
        "limit_bytes": MODEL_SIZE_LIMIT_BYTES,
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "status": "ready",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the pinned AI Airlock embedding model")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "new local model directory; relative paths are anchored to the repository and "
            "existing invalid directories are never overwritten; default: "
            f"{DEFAULT_MODEL_SUBDIR}"
        ),
    )
    return parser


def _fixed_error(error: ModelSetupError) -> NoReturn:
    sys.stderr.write(
        stable_json(
            {
                "schema_version": "0.1",
                "error": {
                    "code": error.code,
                    "message": "The local embedding model could not be prepared safely.",
                },
            }
        )
        + "\n"
    )
    raise SystemExit(1)


def main() -> int:
    try:
        namespace = _parser().parse_args()
        result = prepare_model(namespace.output)
    except ModelSetupError as error:
        _fixed_error(error)
    except Exception:
        _fixed_error(ModelSetupError())
    sys.stdout.write(stable_json(result) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
