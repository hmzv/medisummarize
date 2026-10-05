"""Document metadata returned to the client. Internal storage paths are omitted."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_id: UUID
    original_filename: str
    file_kind: str
    detected_media_type: str
    size_bytes: int
    sha256: str
    status: str
    page_count: int | None = None
    image_width: int | None = None
    image_height: int | None = None
    public_error: str | None = None
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse] = Field(default_factory=list)
