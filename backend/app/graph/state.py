from typing import Any, TypedDict


class TestGenerationState(TypedDict, total=False):
    user_prompt: str
    framework: str
    top_k: int
    user: dict

    plan: str

    retrieved_docs: list[Any]
    retrieved_context_count: int

    status: str
    message: str
    missing: list[str]
    stop_generation: bool

    generated_code: str | None

    valid: bool
    errors: list[str]
    validation_summary: str
    validation_result: dict

    fix_attempts: int