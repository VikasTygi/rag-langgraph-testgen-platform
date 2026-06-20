from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "RAG LangGraph Test Generation Platform"
    api_prefix: str = "/api/v1"

    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "automation_repo"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 1200
    chunk_overlap: int = 200

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    max_fix_attempts: int = 2

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()