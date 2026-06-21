from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.rag.repo_loader import load_repo_as_documents
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

"""
LangChainRAGService is responsible for:
1. Ingesting code repositories and converting them into vector embeddings for retrieval.
2. Searching the ingested repositories based on user queries and returning relevant code snippets and metadata.
"""

class LangChainRAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
        )

        self.vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )

    def ingest_repo(self, repo_path: str, framework: str = "generic") -> dict:
        documents = load_repo_as_documents(
            repo_path=repo_path,
            framework=framework,
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        chunks = splitter.split_documents(documents)

        if chunks:
            self.vector_store.add_documents(chunks)

        logger.info(
            "Indexed files=%s chunks=%s",
            len(documents),
            len(chunks),
        )

        return {
            "indexed_files": len(documents),
            "indexed_chunks": len(chunks),
            "files_loaded": len(documents),
            "chunks_stored": len(chunks),
            "sample_files": [
                doc.metadata.get("source", "")
                for doc in documents[:5]
            ],
        }

    def search(
        self,
        query: str,
        framework: str = "generic",
        top_k: int = 4,
    ) -> List[Document]:
        search_query = f"""
Framework: {framework}

User request:
{query}

Find relevant automation examples, reusable keywords, test cases,
page objects, API payloads, locators, setup steps, and validation logic.
"""

        # Ask for more results first, then filter.
        # This avoids Chroma returning 3 non-Robot chunks and then filtering all out.
        raw_docs = self.vector_store.similarity_search(
            search_query,
            k=max(top_k * 5, 15),
        )

        if not raw_docs:
            return []

        if framework and framework != "generic":
            framework = framework.lower()

            filtered_docs = [
                doc
                for doc in raw_docs
                if doc.metadata.get("framework", "").lower() in [framework, "generic"]
            ]

            if filtered_docs:
                return filtered_docs[:top_k]

        return raw_docs[:top_k]

    def search_as_dict(
        self,
        query: str,
        framework: str = "generic",
        top_k: int = 4,
        user: dict | None = None,
    ):
        results = self.search(
            query=query,
            framework=framework,
            top_k=top_k,
        )

        return {
            "query": query,
            "framework": framework,
            "top_k": top_k,
            "searched_by": user.get("sub") or user.get("username") if user else None,
            "role": user.get("role") if user else None,
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in results
            ],
        }