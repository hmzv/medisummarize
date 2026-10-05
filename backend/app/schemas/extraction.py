"""Extracted-page response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExtractedPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    page_number: int
    text: str
    extraction_method: str
    ocr_confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class ExtractedPageListResponse(BaseModel):
    document_id: UUID
    status: str
    public_error: str | None = None
    items: list[ExtractedPageResponse]
