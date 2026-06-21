from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str


class IngestRequest(BaseModel):
    repo_path: str
    framework: Optional[str] = "generic"


class IngestResponse(BaseModel):
    indexed_files: int
    indexed_chunks: int
    message: str


class SearchRequest(BaseModel):
    query: str
    framework: str = "generic"
    top_k: int = 4


class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    framework: str
    results: List[SearchResult]


class GenerateRequest(BaseModel):
    user_prompt: str
    framework: str = "generic"
    top_k: int = 3


class GenerateResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    missing: list[str] = Field(default_factory=list)

    framework: Optional[str] = None
    user_prompt: Optional[str] = None
    plan: Optional[str] = None
    retrieved_context_count: int = 0
    generated_code: Optional[str] = None
    validation_result: dict[str, Any] | None = None
    valid: bool = False
    errors: list[str] = []
    fix_attempts: int = 0
    validation_summary: str | None = None