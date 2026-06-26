from enum import StrEnum


class EventType(StrEnum):
    GENERATION_REQUESTED = "generation_requested"
    GENERATION_STARTED = "generation_started"
    GENERATION_SUCCEEDED = "generation_succeeded"
    GENERATION_FAILED = "generation_failed"

    PROMPT_BLOCKED = "prompt_blocked"
    SECRET_SCAN_FAILED = "secret_scan_failed"
    CONTEXT_NOT_FOUND = "context_not_found"
    USER_RATE_LIMITED = "user_rate_limited"