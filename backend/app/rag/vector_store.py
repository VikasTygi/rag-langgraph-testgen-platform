import hashlib
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "test_generation_docs"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store():
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=get_embeddings(),
    )


def _doc_id(doc: Document, index: int) -> str:
    source = doc.metadata.get("source", "unknown")
    content_hash = hashlib.md5(doc.page_content.encode("utf-8")).hexdigest()
    return f"{source}:{index}:{content_hash}"


def add_documents_to_store(documents: List[Document]) -> int:
    if not documents:
        return 0

    vector_store = get_vector_store()
    ids = [_doc_id(doc, index) for index, doc in enumerate(documents)]
    vector_store.add_documents(documents=documents, ids=ids)
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
    vector_store = get_vector_store()
    return vector_store._collection.count()
