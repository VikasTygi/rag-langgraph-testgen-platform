from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.auth.dependencies import require_permission
from app.rag.langchain_rag import LangChainRAGService
from app.security.prompt_guard import validate_prompt
from app.security.secret_scanner import SecretScanError


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
def ingest_repo(
    request: RagIngestRequest,
    current_user: dict = Depends(require_permission("rag:ingest")),
):
    try:
        rag_service = LangChainRAGService()

        result = rag_service.ingest_repo(
            repo_path=request.repo_path,
            framework=request.framework,
        )

        files_loaded = result.get("files_loaded", result.get("indexed_files", 0))
        chunks_stored = result.get("chunks_stored", result.get("indexed_chunks", 0))

        return {
            "status": "success",
            "repo_path": request.repo_path,
            "framework": request.framework,
            "secret_scanned": result.get("secret_scanned", True),
            "files_loaded": result["files_loaded"],
            "chunks_stored": result["chunks_stored"],
            "sample_files": result["sample_files"],
            "ingested_by": current_user.get("username"),
            "role": current_user.get("role"),
        # Old keys expected by tests
            "indexed_files": files_loaded,
            "indexed_chunks": chunks_stored,

        }

    except SecretScanError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "blocked",
                "reason": "Secret scanning failed. Repository contains secrets and was not embedded.",
                "blocked_files": exc.result.blocked_files,
                "findings": [
                    {
                        "file_path": finding.file_path,
                        "line_number": finding.line_number,
                        "secret_type": finding.secret_type,
                        "fingerprint": finding.fingerprint,
                    }
                    for finding in exc.result.findings
                ],
                "message": "Remove secrets before ingestion. Actual secret values are never returned.",
            },
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/search")
def search_repo(
    request: RagSearchRequest,
    current_user: dict = Depends(require_permission("rag:search")),
):
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
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )