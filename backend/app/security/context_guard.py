def _get_metadata(doc):
    if isinstance(doc, dict):
        return doc.get("metadata", {}) or {}
    return getattr(doc, "metadata", {}) or {}

def _default_missing_items():
    return [
        "login flow",
        "venue creation keyword",
        "verification logic",
    ]


def control_rag_context(docs, user_prompt, framework, user):
    if not docs:
        message = "No relevant RAG context found."
        return {
            "allowed": False,
            "status": "need_more_context",
            "reason": "No relevant RAG context found.",
            "message": message,
            "missing": _default_missing_items(),
            "docs": [],
            "safe_docs": [],
            "retrieved_context_count": 0,
        }

    safe_docs = []

    user_projects = set(user.get("projects", []))
    user_teams = set(user.get("teams", []))
    user_repos = set(user.get("repos", []))
    user_access_levels = set(user.get("access_levels", []))

    for doc in docs:
        metadata = _get_metadata(doc)

        doc_framework = metadata.get("framework")
        doc_repo = metadata.get("repo")
        doc_project = metadata.get("project")
        doc_team = metadata.get("team")
        doc_access_level = metadata.get("access_level")

        if doc_framework and doc_framework not in [framework, "generic"]:
            continue

        if doc_repo and doc_repo not in user_repos:
            continue

        if doc_project and doc_project not in user_projects:
            continue

        if doc_team and doc_team not in user_teams:
            continue

        if doc_access_level and doc_access_level not in user_access_levels:
            continue

        safe_docs.append(doc)

    if not safe_docs:
        message =  "No authorized RAG context found."
        return {
            "message": message,
            "allowed": False,
            "status": "need_more_context",
            "reason": "No authorized RAG context found.",
            "missing": _default_missing_items(),
            "docs": [],
            "safe_docs": [],
            "retrieved_context_count": 0,
        }

    message = "Authorized RAG context is available."
    return {
        "message": message,
        "allowed": True,
        "status": "context_ready",
        "reason": "Authorized RAG context is available.",
        "missing": [],
        "docs": safe_docs,
        "safe_docs": safe_docs,
        "retrieved_context_count": len(safe_docs),
    }
