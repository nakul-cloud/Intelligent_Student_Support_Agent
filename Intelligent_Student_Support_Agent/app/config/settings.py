"""Application configuration loaded from environment variables using Pydantic Settings.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for loading, validating,
  and providing typed application settings from environment variables and .env.
- Open/Closed (OCP): New configuration fields are added here as typed properties
  without modifying dependent consumer modules.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Intelligent Student Support Agent."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM Settings (Groq / OpenAI-compatible endpoint) ---
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "qwen/qwen3.8-27b"
    openai_api_key: str = ""
    agent_max_turns: int = 6
    agent_temperature: float = 0.1

    # --- Local Embedding Settings (HuggingFace SentenceTransformers) ---
    embedding_model: str = "Orange/orange-nomic-v1.5-1536"
    embedding_dimensions: int = 1536

    # --- Vector Database (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "student_handbook"
    similarity_threshold: float = 0.45
    top_k_chunks: int = 3

    # --- Dynamic RAG Chunking Configuration ---
    chunk_target_tokens: int = 500
    chunk_overlap_tokens: int = 50
    chunk_target_chars: int = 1800
    chunk_overlap_chars: int = 200

    # --- RAG Cross-Encoder Re-Ranker Configuration ---
    reranker_enabled: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_n: int = 15
    reranker_top_k: int = 3
    reranker_batch_size: int = 8
    reranker_device: str = "cpu"


    # --- Relational Database (PostgreSQL Async) & Cache (Redis) ---
    database_url: str = (
        "postgresql+asyncpg://student_agent:student_agent_dev@localhost:5432/student_support_db"
    )
    redis_host: str = "localhost"
    redis_port: int = 6379

    # --- File Paths & Domain Identifiers ---
    handbook_path: str = "data/student_handbook.pdf"
    traces_dir: str = "traces"
    ticket_prefix: str = "TICK-"

    # --- Observability (Optional LangSmith Remote Dashboard) ---
    enable_langsmith: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "student-support-agent"

    # --- Authentication (JWT & Password Hashing) ---
    jwt_secret: str = "super-secret-jwt-key-256-bit-student-agent"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # --- Two-Tier Memory Configuration ---
    redis_memory_key_prefix: str = "student_memory:"
    redis_memory_ttl_seconds: int = 86400

    # --- Privacy & Safety Settings ---
    sensitive_keywords_str: str = (
        "password,otp,pin,cvv,credit_card,card_number,secret,ssn,token,bank,upi"
    )

    # --- Sensitive Actions requiring Approval Gate ---
    sensitive_actions_str: str = (
        "update_contact,request_fee_waiver,update_address,scholarship_appeal"
    )

    @property
    def sensitive_keywords(self) -> frozenset[str]:
        """Parsed set of sensitive keywords to scrub from long-term memory."""
        return frozenset(
            k.strip().lower() for k in self.sensitive_keywords_str.split(",") if k.strip()
        )

    @property
    def sensitive_actions(self) -> frozenset[str]:
        """Parsed set of sensitive actions requiring approval confirmation."""
        return frozenset(
            a.strip() for a in self.sensitive_actions_str.split(",") if a.strip()
        )

    # --- Connection Pool Tuning ---
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # --- Security & CORS Settings ---
    allowed_origins_str: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        if self.app_env == "development" and not self.allowed_origins_str:
            return ["*"]
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]

    # --- Application Runtime & Logging ---
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    rate_limit_chat_per_minute: int = 30
    rate_limit_auth_per_minute: int = 20


# Export singleton settings instance
settings = Settings()

