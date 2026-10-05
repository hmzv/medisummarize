"""Structured summary schemas. Citation IDs are presence checks, not clinical proof."""

from typing import Literal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

DISCLAIMER = (
    "Research prototype for clinical-document summarization only. "
    "Not for diagnosis, prescribing, treatment recommendations, or autonomous "
    "clinical decision-making. Verify all generated information against the original records."
)

EvidenceStatus = Literal["citation_present", "needs_review"]


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus = "needs_review"

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Claim text cannot be empty")
        return value.strip()


class StructuredSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key_history: list[Claim] = Field(default_factory=list)
    current_documented_findings: list[Claim] = Field(default_factory=list)
    medications: list[Claim] = Field(default_factory=list)
    allergies: list[Claim] = Field(default_factory=list)
    laboratory_findings: list[Claim] = Field(default_factory=list)
    unresolved_or_unavailable: list[str] = Field(default_factory=list)
    processing_limitations: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER


class EvidencePassage(BaseModel):
    id: str
    document_id: str
    original_filename: str
    page: int
    method: str
    text: str


class SummaryResponse(BaseModel):
    id: UUID
    record_id: UUID
    summary: StructuredSummary
    evidence: list[EvidencePassage]
    prompt_version: str
    generation_provider: str
    generation_model: str
    embedding_model: str
    is_mock: bool
    validation_warnings: list[str]
    created_at: datetime
