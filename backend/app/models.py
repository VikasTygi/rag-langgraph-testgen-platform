from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
    prompt: str
    framework: str = "robot"
    top_k: int = 4


class GenerateResponse(BaseModel):
    framework: str
    user_prompt: str
    plan: str
    retrieved_context_count: int
    generated_code: str
    valid: bool
    errors: List[str]
    fix_attempts: int
    validation_summary: str