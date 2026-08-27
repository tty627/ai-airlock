from __future__ import annotations

import pytest

from airlock.capsule.leak_guard import enforce_no_sensitive_leaks, find_sensitive_leaks
from airlock.errors import LeakageGuardError


def test_leak_guard_checks_case_and_phone_normalization() -> None:
    values = {"SecretValueABC", "+86 138-0000-1234"}

    assert find_sensitive_leaks(["safe [API_KEY] [PHONE_001]"], values) == 0
    assert find_sensitive_leaks(["secretvalueabc"], values) == 1
    assert find_sensitive_leaks(["8613800001234"], values) == 1


def test_leak_guard_raises_input_independent_error() -> None:
    with pytest.raises(LeakageGuardError) as captured:
        enforce_no_sensitive_leaks(["contains sk-test-danger"], {"sk-test-danger"})

    assert "sk-test-danger" not in repr(captured.value)
