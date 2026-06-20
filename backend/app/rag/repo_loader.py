from pathlib import Path
from typing import List

from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {
    ".robot",
    ".py",
    ".ts",
    ".js",
    ".txt",
    ".md",
}


def detect_framework(file_path: Path, default_framework: str) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".robot":
        return "robot"

    if suffix == ".py":
        return "python"

    if suffix in [".ts", ".js"]:
        return "playwright"

    return default_framework


def load_repo_as_documents(repo_path: str, framework: str = "generic") -> List[Document]:
    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo_path}")

    documents: List[Document] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")

        if not content.strip():
            continue

        detected_framework = detect_framework(file_path, framework)

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "file_name": file_path.name,
                    "extension": file_path.suffix,
                    "framework": detected_framework,
                },
            )
        )

        logger.info("Loaded document: %s", file_path)

    return documents