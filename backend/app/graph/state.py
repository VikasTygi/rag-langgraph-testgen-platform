from typing import List, TypedDict

from langchain_core.documents import Document


class TestGenerationState(TypedDict):
    user_prompt: str
    framework: str
    top_k: int

    plan: str
    retrieved_docs: List[Document]
    generated_code: str

    valid: bool
    errors: List[str]
    validation_summary: str

    fix_attempts: int