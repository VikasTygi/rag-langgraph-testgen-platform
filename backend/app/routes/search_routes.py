from fastapi import APIRouter, HTTPException

from app.models import SearchRequest, SearchResponse, SearchResult
from app.rag.langchain_rag import LangChainRAGService

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search_repo(request: SearchRequest):
    try:
        rag_service = LangChainRAGService()

        docs = rag_service.search(
            query=request.query,
            framework=request.framework,
            top_k=request.top_k,
        )

        results = [
            SearchResult(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in docs
        ]

        return SearchResponse(
            query=request.query,
            framework=request.framework,
            results=results,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))