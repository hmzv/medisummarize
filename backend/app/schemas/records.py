"""Patient-record container schemas. Ownership is never accepted from the client."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SYNTHETIC_NOTICE = (
    "SYNTHETIC — NOT A REAL PATIENT. De-identified demonstration container only."
)


class RecordCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_label: str = Field(min_length=1, max_length=120)


class RecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_label: str
    created_at: datetime
    updated_at: datetime
    synthetic_notice: str = SYNTHETIC_NOTICE


class RecordListResponse(BaseModel):
    items: list[RecordResponse]
