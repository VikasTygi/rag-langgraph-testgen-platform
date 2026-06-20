from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.vector_store import add_documents_to_store


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

    documents: List[Document] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix not in ALLOWED_EXTENSIONS:
            continue

        detected_framework = detect_framework(file_path)

        if framework.lower() != "generic" and framework.lower() != detected_framework:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if not content.strip():
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "framework": detected_framework,
                    "file_name": file_path.name,
                },
            )
        )

    return documents


def ingest_repository(repo_path: str, framework: str = "generic") -> dict:
    raw_documents = load_repo_documents(repo_path, framework)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
    )

    chunks = splitter.split_documents(raw_documents)
    stored_count = add_documents_to_store(chunks)

    return {
        "status": "success",
        "repo_path": repo_path,
        "framework": framework,
        "files_loaded": len(raw_documents),
        "chunks_stored": stored_count,
        "sample_files": [doc.metadata["source"] for doc in raw_documents[:10]],
    }
