"""Safe, input-independent errors exposed by the CLI."""

from __future__ import annotations


class AirlockError(Exception):
    """Base class for errors that are safe to expose by code only."""

    code = "AIRLOCK_ERROR"
    public_message = "AI Airlock could not complete the request safely."

    def __init__(self) -> None:
        super().__init__(self.public_message)


class InputIncompleteError(AirlockError):
    code = "INPUT_INCOMPLETE"
    public_message = "The input could not be scanned completely; no result was released."


class ConfigurationError(AirlockError):
    code = "INVALID_CONFIGURATION"
    public_message = "The policy configuration is invalid."


class UnsafeTaskError(AirlockError):
    code = "TASK_BLOCKED"
    public_message = "The task violates the active disclosure policy."


class NoSafeContextError(AirlockError):
    code = "NO_SAFE_CONTEXT"
    public_message = "No safe context could be released for this task."


class PolicyLimitError(AirlockError):
    code = "POLICY_LIMIT_EXCEEDED"
    public_message = "A policy limit prevented safe result generation."


class LeakageGuardError(AirlockError):
    code = "LEAKAGE_GUARD_FAILED"
    public_message = "The output safety check failed; no result was released."
