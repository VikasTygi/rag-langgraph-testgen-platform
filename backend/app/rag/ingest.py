from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vector_store import add_documents_to_store
from app.rag.repo_metadata import resolve_repo_metadata
from app.security.secret_scanner import assert_no_secrets_before_ingest


ALLOWED_EXTENSIONS = {
    ".robot",
    ".py",
    ".ts",
    ".js",
    ".txt",
    ".md",
}


def detect_framework(file_path: Path) -> str:
    if file_path.suffix == ".robot":
        return "robot"

    if file_path.suffix == ".py":
        return "pytest"

    if file_path.suffix in [".ts", ".js"]:
        return "playwright"

    return "generic"


def load_repo_documents(repo_path: str, framework: str = "generic") -> List[Document]:
    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repo path not found: {repo_path}")

    # IMPORTANT:
    # Secret scanning happens before:
    # - LangChain Document creation
    # - text splitting
    # - embeddings
    # - ChromaDB storage
    safe_files = assert_no_secrets_before_ingest(repo_path)

    documents: List[Document] = []

    for file_path in safe_files:
        if file_path.suffix not in ALLOWED_EXTENSIONS:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        metadata = resolve_repo_metadata(
            file_path=str(file_path),
            default_framework=framework,
        )

        metadata["secret_scanned"] = True
        metadata["detected_framework"] = detect_framework(file_path)

        documents.append(
            Document(
                page_content=content,
                metadata=metadata,
            )
        )

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["secret_scanned"] = True

    return chunks


def ingest_repository(repo_path: str, framework: str = "generic") -> dict:
    raw_documents = load_repo_documents(repo_path, framework)

    chunks = split_documents(raw_documents)

    stored_count = add_documents_to_store(chunks)

    return {
        "status": "success",
        "repo_path": repo_path,
        "framework": framework,
        "secret_scanned": True,
        "files_loaded": len(raw_documents),
        "chunks_stored": stored_count,
        "sample_files": [doc.metadata["source"] for doc in raw_documents[:10]],
    }