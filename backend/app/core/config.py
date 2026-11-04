"""
Configuration Management for DebugGraph AI.
Loads application settings and environment variables using Pydantic Settings.
"""
from functools import lru_cache
from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema and environment variable loader."""

    # Application Information
    APP_NAME: str = "DebugGraph AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # AI / LLM Configuration (never hardcode secrets)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_OUTPUT_TOKENS: int = 4096

    # Relational Database (PostgreSQL)
    DATABASE_URL: Optional[str] = None

    # Embedding & Vector Model Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    VECTOR_SIZE: int = 384
    DEFAULT_SEARCH_TOP_K: int = 5

    # Hybrid Retrieval & Reranking Configuration
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RRF_K: int = 60
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    RERANKER_DEVICE: str = "cpu"
    HYBRID_RETRIEVAL_CANDIDATE_K: int = 20

    # Vector Database (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "debuggraph_logs"
    QDRANT_API_KEY: Optional[str] = None

    # Graph Database (Neo4j)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: Optional[str] = None
    NEO4J_DATABASE: str = "neo4j"

    # GitHub Repository & Commit Intelligence
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"

    # CORS and Network Configuration
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Logging & File Uploads
    LOG_LEVEL: str = "INFO"
    MAX_LOG_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB maximum upload size

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from a comma-separated string or list."""
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:5173", "http://localhost:3000"]

    @model_validator(mode="before")
    @classmethod
    def populate_fallback_keys(cls, values: Any) -> Any:
        """Handle alternate environment variable names (e.g., APP_DEBUG -> DEBUG, CORS_ORIGINS -> ALLOWED_ORIGINS)."""
        if isinstance(values, dict):
            # APP_DEBUG -> DEBUG
            if "DEBUG" not in values and "APP_DEBUG" in values:
                raw_debug = values.get("APP_DEBUG")
                if isinstance(raw_debug, str):
                    values["DEBUG"] = raw_debug.lower() in ("true", "1", "yes", "on")
                else:
                    values["DEBUG"] = bool(raw_debug)

            # CORS_ORIGINS -> ALLOWED_ORIGINS
            if "ALLOWED_ORIGINS" not in values and "CORS_ORIGINS" in values:
                values["ALLOWED_ORIGINS"] = values["CORS_ORIGINS"]

            # EMBEDDING_MODEL_NAME -> EMBEDDING_MODEL
            if "EMBEDDING_MODEL" not in values and "EMBEDDING_MODEL_NAME" in values:
                values["EMBEDDING_MODEL"] = values["EMBEDDING_MODEL_NAME"]

            # RERANKER_MODEL_NAME / CROSS_ENCODER_MODEL_NAME -> RERANKER_MODEL
            if "RERANKER_MODEL" not in values:
                if "RERANKER_MODEL_NAME" in values:
                    values["RERANKER_MODEL"] = values["RERANKER_MODEL_NAME"]
                elif "CROSS_ENCODER_MODEL_NAME" in values:
                    values["RERANKER_MODEL"] = values["CROSS_ENCODER_MODEL_NAME"]

            # CROSS_ENCODER_DEVICE -> RERANKER_DEVICE
            if "RERANKER_DEVICE" not in values and "CROSS_ENCODER_DEVICE" in values:
                values["RERANKER_DEVICE"] = values["CROSS_ENCODER_DEVICE"]

            # QDRANT_HOST / QDRANT_PORT -> QDRANT_URL
            if "QDRANT_URL" not in values and "QDRANT_HOST" in values:
                host = values.get("QDRANT_HOST", "localhost")
                port = values.get("QDRANT_PORT", "6333")
                values["QDRANT_URL"] = f"http://{host}:{port}"

            # NEO4J_URL -> NEO4J_URI
            if "NEO4J_URI" not in values and "NEO4J_URL" in values:
                values["NEO4J_URI"] = values["NEO4J_URL"]

            # GITHUB_PAT / GITHUB_ACCESS_TOKEN -> GITHUB_TOKEN
            if "GITHUB_TOKEN" not in values:
                if "GITHUB_PAT" in values:
                    values["GITHUB_TOKEN"] = values["GITHUB_PAT"]
                elif "GITHUB_ACCESS_TOKEN" in values:
                    values["GITHUB_TOKEN"] = values["GITHUB_ACCESS_TOKEN"]

        return values


@lru_cache()
def get_settings() -> Settings:
    """Retrieve and cache settings singleton instance."""
    return Settings()


# Global settings instance
settings = get_settings()

