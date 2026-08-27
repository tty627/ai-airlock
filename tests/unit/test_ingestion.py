from __future__ import annotations

from pathlib import Path

import pytest

from airlock.ingestion import IngestionLimits, InputIncomplete, load_path, loader


def test_loads_supported_files_env_variants_and_bom_in_stable_order(tmp_path: Path) -> None:
    (tmp_path / "z.log").write_text("last", encoding="utf-8")
    (tmp_path / ".env.example").write_bytes(b"\xef\xbb\xbfTOKEN=test")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "a.yaml").write_text("first: true", encoding="utf-8")
    (nested / "raw.bin").write_bytes(b"\x00\x01")

    result = load_path(tmp_path)

    assert [item.relative_path for item in result.files] == [
        ".env.example",
        "nested/a.yaml",
        "z.log",
    ]
    assert result.files[0].text == "TOKEN=test"
    assert result.inspected_files == 3
    assert result.skipped_files == 1
    assert result.total_bytes == sum(item.byte_size for item in result.files)


def test_single_supported_file_uses_only_its_name(tmp_path: Path) -> None:
    source = tmp_path / "service.log"
    source.write_text("ERROR", encoding="utf-8")

    result = load_path(source)

    assert result.files[0].relative_path == "service.log"


def test_external_symlink_is_never_read(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.log"
    outside.write_text("must-not-be-read", encoding="utf-8")
    link = tmp_path / "outside.log"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")

    result = load_path(tmp_path)

    assert result.files == ()
    assert result.skipped_files == 1
    assert "must-not-be-read" not in repr(result)


@pytest.mark.parametrize("payload", [b"\xff\xfe\x00", b"ok\xffbad"])
def test_non_utf8_supported_file_fails_closed(tmp_path: Path, payload: bytes) -> None:
    (tmp_path / "bad.log").write_bytes(payload)

    with pytest.raises(InputIncomplete, match="^INPUT_INCOMPLETE$"):
        load_path(tmp_path)


def test_file_count_limit_fails_whole_load(tmp_path: Path) -> None:
    (tmp_path / "a.log").write_text("a", encoding="utf-8")
    (tmp_path / "b.log").write_text("b", encoding="utf-8")

    with pytest.raises(InputIncomplete):
        load_path(
            tmp_path,
            IngestionLimits(max_files=1, max_file_bytes=10, max_total_bytes=10),
        )


def test_per_file_and_total_byte_limits_fail_closed(tmp_path: Path) -> None:
    (tmp_path / "a.log").write_text("123456", encoding="utf-8")
    with pytest.raises(InputIncomplete):
        load_path(
            tmp_path,
            IngestionLimits(max_files=2, max_file_bytes=5, max_total_bytes=10),
        )

    (tmp_path / "a.log").write_text("1234", encoding="utf-8")
    (tmp_path / "b.log").write_text("5678", encoding="utf-8")
    with pytest.raises(InputIncomplete):
        load_path(
            tmp_path,
            IngestionLimits(max_files=2, max_file_bytes=6, max_total_bytes=7),
        )


def test_unknown_single_file_is_counted_as_skipped(tmp_path: Path) -> None:
    source = tmp_path / "image.bin"
    source.write_bytes(b"opaque")

    result = load_path(source)

    assert result.inspected_files == 0
    assert result.skipped_files == 1


def test_missing_or_symlink_root_has_fixed_safe_error(tmp_path: Path) -> None:
    missing = tmp_path / "private-name-that-must-not-leak"
    with pytest.raises(InputIncomplete) as captured:
        load_path(missing)
    assert str(captured.value) == "INPUT_INCOMPLETE"
    assert "private-name" not in str(captured.value)


def test_supported_file_read_error_aborts_without_echoing_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "sensitive-customer-name.log"
    source.write_text("safe", encoding="utf-8")

    def denied(*_args, **_kwargs):
        raise PermissionError("sensitive-customer-name.log")

    monkeypatch.setattr(loader.os, "open", denied)
    with pytest.raises(InputIncomplete) as captured:
        load_path(tmp_path)

    assert str(captured.value) == "INPUT_INCOMPLETE"
    assert "customer" not in str(captured.value)


def test_limit_values_must_be_positive_integers() -> None:
    with pytest.raises(ValueError):
        IngestionLimits(max_files=True)
    with pytest.raises(ValueError):
        IngestionLimits(max_file_bytes=0)
    with pytest.raises(ValueError):
        IngestionLimits(max_file_bytes=20, max_total_bytes=10)
