import hashlib
import math
import os
import sys
from functools import lru_cache
from typing import List, Optional

import chromadb
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", os.getenv("CHROMA_DIR", "./chroma_db"))
COLLECTION_NAME = "test_generation_docs"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class FastTestEmbeddings(Embeddings):
    """
    Deterministic local embeddings for tests.

    This avoids HuggingFace network calls during pytest.
    Do not use this for production semantic quality.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension

        for token in text.lower().split():
            token_hash = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            vector[token_hash % self.dimension] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


def _is_test_mode() -> bool:
    return "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None


@lru_cache(maxsize=1)
def get_embeddings():
    if _is_test_mode():
        return FastTestEmbeddings()

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vector_store():
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=get_embeddings(),
    )


def _doc_id(doc: Document, index: int) -> str:
    source = doc.metadata.get("source", "unknown")
    content_hash = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
    return f"{source}:{index}:{content_hash}"


def add_documents_to_store(documents: List[Document]) -> int:
    if not documents:
        return 0

    vector_store = get_vector_store()
    ids = [_doc_id(doc, index) for index, doc in enumerate(documents)]

    vector_store.add_documents(
        documents=documents,
        ids=ids,
    )

    return len(documents)


def search_documents(
    query: str,
    top_k: int = 3,
    framework: Optional[str] = None,
) -> List[Document]:
    vector_store = get_vector_store()

    search_filter = None
    if framework and framework.lower() != "generic":
        search_filter = {"framework": framework.lower()}

    return vector_store.similarity_search(
        query=query,
        k=top_k,
        filter=search_filter,
    )


def count_documents() -> int:
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        collection = client.get_collection(COLLECTION_NAME)
        return collection.count()
    except Exception:
        return 0