from typing import Any

from app.generator.framework_prompts.robot_prompt import build_robot_prompt
from app.generator.framework_prompts.pytest_prompt import build_pytest_prompt
from app.generator.framework_prompts.playwright_prompt import build_playwright_prompt


def docs_to_text(retrieved_docs: Any) -> str:
    """
    Convert retrieved RAG documents into plain text context.
    Supports:
    - list[str]
    - list[LangChain Document]
    - list[dict]
    - single string
    """

    if not retrieved_docs:
        return ""

    if isinstance(retrieved_docs, str):
        return retrieved_docs

    parts = []

    if isinstance(retrieved_docs, list):
        for doc in retrieved_docs:
            if isinstance(doc, str):
                parts.append(doc)
            elif hasattr(doc, "page_content"):
                parts.append(doc.page_content)
            elif isinstance(doc, dict):
                parts.append(
                    doc.get("page_content")
                    or doc.get("content")
                    or doc.get("text")
                    or str(doc)
                )
            else:
                parts.append(str(doc))

        return "\n\n---\n\n".join(parts)

    return str(retrieved_docs)


def build_generation_prompt(
    user_prompt: str,
    framework: str,
    retrieved_context: str = "",
    retrieved_docs: Any = None,
) -> str:
    """
    Build framework-specific generation prompt.
    Accepts both retrieved_context and retrieved_docs so LangGraph/RAG nodes can call it safely.
    """

    framework = framework.lower()

    if retrieved_docs is not None and not retrieved_context:
        retrieved_context = docs_to_text(retrieved_docs)

    if framework == "robot":
        return build_robot_prompt(user_prompt, retrieved_context)

    if framework in ["pytest", "python"]:
        return build_pytest_prompt(user_prompt, retrieved_context)

    if framework in ["playwright", "typescript", "playwright-ts"]:
        return build_playwright_prompt(user_prompt, retrieved_context)

    raise ValueError(f"Unsupported framework: {framework}")
