from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    testing: bool = False
    # App
    app_mode: str = "api"
    app_name: str = "RAG LangGraph TestGen API"
    app_env: str = "local"
    api_prefix: str = "/api/v1"

    log_level: str = "INFO"

    # RAG / Chroma
    chroma_collection_name: str = "rag_testgen_collection"
    chroma_db_dir: str = "./chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./chroma_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Local LLM / Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    max_fix_attempts: int = 2

    # Auth
    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: str = "*"

    # Database
    database_url: str = "sqlite:///./rag_testgen.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    generation_status_ttl_seconds: int = 3600
    user_rate_limit_per_minute: int = 10
    max_active_jobs_per_user: int = 3

    # AWS / SQS
    aws_region: str = "ap-south-1"
    sqs_generation_queue_url: str = ""

    # Kafka
    kafka_enabled: bool = True
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_events_topic: str = "rag-generation-events"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()