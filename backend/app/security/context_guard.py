def get_doc_text(doc) -> str:
    if hasattr(doc, "page_content"):
        return doc.page_content or ""

    if isinstance(doc, dict):
        return (
            doc.get("content")
            or doc.get("page_content")
            or doc.get("text")
            or ""
        )

    return str(doc)


def get_doc_metadata(doc) -> dict:
    if hasattr(doc, "metadata"):
        return doc.metadata or {}

    if isinstance(doc, dict):
        return doc.get("metadata", {}) or {}

    return {}


def control_rag_context(
    docs: list,
    user_prompt: str,
    framework: str,
    user: dict | None = None,
) -> dict:
    if not docs:
        return {
            "allowed": False,
            "message": "No relevant automation context found.",
            "missing": [
                "login flow",
                "venue creation keyword",
                "verification logic",
            ],
            "safe_docs": [],
        }

    safe_docs = []

    for doc in docs:
        text = get_doc_text(doc)
        metadata = get_doc_metadata(doc)

        doc_framework = metadata.get("framework")

        if doc_framework and framework and doc_framework != framework:
            continue

        lower_text = text.lower()

        has_login = "login" in lower_text
        has_venue = "venue" in lower_text
        has_verify = (
            "verify" in lower_text
            or "verification" in lower_text
            or "should be equal" in lower_text
            or "should be true" in lower_text
        )

        if has_login or has_venue or has_verify:
            safe_docs.append(doc)

    if not safe_docs:
        return {
            "allowed": False,
            "message": "No relevant automation context found.",
            "missing": [
                "login flow",
                "venue creation keyword",
                "verification logic",
            ],
            "safe_docs": [],
        }

    return {
        "allowed": True,
        "message": "Controlled RAG context is available.",
        "missing": [],
        "safe_docs": safe_docs,
    }