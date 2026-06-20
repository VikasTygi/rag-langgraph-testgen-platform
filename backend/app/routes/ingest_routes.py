from fastapi import APIRouter, HTTPException

from app.models import IngestRequest, IngestResponse
from app.rag.langchain_rag import LangChainRAGService

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_repo(request: IngestRequest):
    try:
        rag_service = LangChainRAGService()

        result = rag_service.ingest_repo(
            repo_path=request.repo_path,
            framework=request.framework,
        )

        return IngestResponse(
            indexed_files=result["indexed_files"],
            indexed_chunks=result["indexed_chunks"],
            message="Repository indexed successfully using LangChain + ChromaDB",
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))