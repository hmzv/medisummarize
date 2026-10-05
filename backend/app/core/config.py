"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings. Missing required values fail at import/startup."""

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(BACKEND_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="MediSummarize AI", validation_alias="APP_NAME")
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    secret_key: str = Field(validation_alias="SECRET_KEY")
    database_url: str = Field(validation_alias="DATABASE_URL")
    cors_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )
    api_prefix: str = "/api/v1"
    storage_dir: Path = Field(default=Path("./storage"), validation_alias="STORAGE_DIR")
    access_token_expire_minutes: int = Field(
        default=480,
        ge=5,
        le=24 * 60,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_algorithm: str = "HS256"
    max_upload_bytes: int = Field(default=15 * 1024 * 1024, validation_alias="MAX_UPLOAD_BYTES")
    max_pdf_pages: int = Field(default=50, validation_alias="MAX_PDF_PAGES")
    max_image_pixels: int = Field(default=40_000_000, validation_alias="MAX_IMAGE_PIXELS")
    max_image_side: int = Field(default=8000, validation_alias="MAX_IMAGE_SIDE")
    max_text_bytes: int = Field(default=2 * 1024 * 1024, validation_alias="MAX_TEXT_BYTES")
    extract_on_upload: bool = Field(default=True, validation_alias="EXTRACT_ON_UPLOAD")
    chunk_size: int = Field(default=800, ge=50, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, ge=0, validation_alias="CHUNK_OVERLAP")
    embedding_provider: str = Field(default="hashed_token", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="EMBEDDING_MODEL",
    )
    index_dir: Path = Field(default=Path("./data/indexes"), validation_alias="INDEX_DIR")
    retrieval_top_k: int = Field(default=8, ge=1, le=50, validation_alias="RETRIEVAL_TOP_K")
    generation_provider: str = Field(default="mock", validation_alias="GENERATION_PROVIDER")
    generation_base_url: str = Field(
        default="http://127.0.0.1:11434/v1",
        validation_alias="GENERATION_BASE_URL",
    )
    generation_model: str = Field(default="llama3.1:8b", validation_alias="GENERATION_MODEL")
    generation_timeout_seconds: float = Field(default=60, validation_alias="GENERATION_TIMEOUT_SECONDS")
    generation_max_output_tokens: int = Field(default=800, validation_alias="GENERATION_MAX_OUTPUT_TOKENS")

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_nonempty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("SECRET_KEY must be a non-empty string")
        return value

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_nonempty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("DATABASE_URL must be a non-empty SQLAlchemy URL")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        if any(origin == "*" for origin in origins):
            raise ValueError("Wildcard CORS origins are not allowed")
        return origins

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def resolved_index_dir(self) -> Path:
        path = self.index_dir
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path.resolve()

    @property
    def resolved_storage_dir(self) -> Path:
        path = self.storage_dir
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Test helper so settings can be reloaded after environment changes."""
    get_settings.cache_clear()
