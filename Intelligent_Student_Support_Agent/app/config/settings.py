"""Application configuration loaded from environment variables using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Intelligent Student Support Agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM Settings (Groq) ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Embedding Settings ---
    openai_api_key: str = ""
    embedding_model: str = "Orange/orange-nomic-v1.5-1536"
    embedding_dimensions: int = 1536

    # --- Vector Database (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    similarity_threshold: float = 0.7
    top_k_chunks: int = 3

    # --- Dynamic RAG Chunking Configuration ---
    chunk_target_tokens: int = 500
    chunk_overlap_tokens: int = 50
    chunk_target_chars: int = 1800
    chunk_overlap_chars: int = 200

    # --- Relational Database & Cache ---
    database_url: str = (
        "postgresql+asyncpg://student_agent:student_agent_dev@localhost:5432/student_support_db"
    )
    redis_host: str = "localhost"
    redis_port: int = 6379

    # --- Ingestion File Path ---
    handbook_path: str = "data/student_handbook.pdf"

    # --- Observability (LangSmith & Local Tracer) ---
    enable_langsmith: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "student-support-agent"

    # --- Application Runtime ---
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


# Export singleton settings instance
settings = Settings()
