"""Health-check response models."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "medisummarize-ai"
    environment: str = Field(min_length=1)


class ReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"
    database: Literal["connected"] = "connected"


class GenerationHealthResponse(BaseModel):
    status: str
    provider: str
    is_mock: bool
    warning: str | None = None
