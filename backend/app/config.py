"""
Centralized application configuration.

All secrets and tunables are read from environment variables (see .env.example).
Using pydantic-settings gives us validation + sane defaults in one place.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API keys 
    groq_api_key: str = ""
    huggingfacehub_api_token: str = ""

    # Models
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.2

    # Multilingual (Hindi + English) sentence-embedding model served through
    # the Hugging Face Inference API via `langchain-huggingface`.
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_provider: str = "hf-inference"

    # RAG tuning
    chunk_size: int = 900
    chunk_overlap: int = 150
    retriever_k: int = 5

    # Session store
    session_ttl_minutes: int = 120
    max_sessions: int = 200

    # App / CORS
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
