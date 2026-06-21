from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi import Depends
from app.auth.dependencies import require_permission

from app.rag.langchain_rag import LangChainRAGService
from app.security.prompt_guard import validate_prompt

router = APIRouter()


class RagIngestRequest(BaseModel):
    repo_path: str
    framework: Optional[str] = "generic"


class RagSearchRequest(BaseModel):
    query: str
    framework: Optional[str] = "generic"
    top_k: int = 4


@router.get("/status")
def rag_status():
    return {
        "status": "ok",
        "service": "rag status call",
    }


@router.post("/ingest")
def ingest_repo(request: RagIngestRequest, current_user: dict = Depends(require_permission("rag:ingest"))):
    try:
        rag_service = LangChainRAGService()

        result = rag_service.ingest_repo(
            repo_path=request.repo_path,
            framework=request.framework,
        )

        return {
            "status": "success",
            "repo_path": request.repo_path,
            "framework": request.framework,
            "files_loaded": result["files_loaded"],
            "chunks_stored": result["chunks_stored"],
            "sample_files": result["sample_files"],
            "user": current_user,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/search")
def search_repo(request: RagSearchRequest, current_user: dict = Depends(require_permission("rag:search"))):
    
        # Validate user query before RAG/vector search
    guard_result = validate_prompt(request.query)

    if not guard_result["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=guard_result,
        )

    
    try:
        rag_service = LangChainRAGService()

        return rag_service.search_as_dict(
            query=request.query,
            framework=request.framework,
            top_k=request.top_k,
            user=current_user,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))