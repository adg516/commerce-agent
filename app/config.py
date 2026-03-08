from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    catalogs_root: str = "data/catalogs"
    default_catalog_slug: str = "athletic"
    host: str = "0.0.0.0"
    port: int = 8000
    # SCALE: add settings for external services as you scale out:
    # redis_url: str = ""                  # conversation store, embedding cache, pub/sub
    # database_url: str = ""               # PostgreSQL for products, users, analytics
    # vector_db_url: str = ""              # Pinecone/Qdrant/pgvector endpoint
    # s3_bucket: str = ""                  # catalog file + image storage
    # celery_broker_url: str = ""          # async task queue for heavy operations
    # sentry_dsn: str = ""                 # error tracking
    # otel_exporter_endpoint: str = ""     # OpenTelemetry traces

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_catalogs_root(self) -> Path:
        return BASE_DIR / self.catalogs_root

    @property
    def resolved_catalog_path(self) -> Path:
        return self.resolved_catalogs_root / self.default_catalog_slug / "catalog.json"

    @property
    def resolved_embeddings_path(self) -> Path:
        return self.resolved_catalogs_root / self.default_catalog_slug / "embeddings.npy"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
