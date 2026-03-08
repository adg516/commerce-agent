from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    catalog_path: str = "data/catalog.json"
    embeddings_path: str = "data/embeddings.npy"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_catalog_path(self) -> Path:
        return BASE_DIR / self.catalog_path

    @property
    def resolved_embeddings_path(self) -> Path:
        return BASE_DIR / self.embeddings_path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
