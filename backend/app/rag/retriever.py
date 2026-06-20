from typing import List

from langchain_core.documents import Document

from app.rag.langchain_rag import LangChainRAGService


class AutomationRetriever:
    def __init__(self):
        self.rag_service = LangChainRAGService()

    def retrieve(self, prompt: str, framework: str, top_k: int = 4) -> List[Document]:
        return self.rag_service.search(
            query=prompt,
            framework=framework,
            top_k=top_k,
        )