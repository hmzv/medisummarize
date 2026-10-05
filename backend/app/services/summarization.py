"""RAG summarization with citation validation. Citations are not clinical proof."""

from __future__ import annotations

import json
import uuid

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.summary import Summary
from app.prompts.summarize_v1 import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from app.schemas.summaries import Claim, EvidencePassage, StructuredSummary, SummaryResponse
from app.services.embeddings.providers import get_embedding_provider
from app.services.generation.providers import get_generation_provider
from app.services.records import get_owned_record
from app.services.retrieval.service import retrieve_for_record

SECTION_QUERIES = [
    ("key history", "past medical history diagnoses procedures timeline"),
    ("current findings", "current documented findings symptoms examination"),
    ("medications", "medications prescriptions doses"),
    ("allergies", "allergies adverse drug reactions"),
    ("laboratory findings", "laboratory results units dates"),
]


def generate_record_summary(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> SummaryResponse:
    record = get_owned_record(db, record_id, owner_id)
    provider = get_generation_provider()
    embedding = get_embedding_provider()
    evidence_rows: dict[uuid.UUID, Chunk] = {}
    section_notes: list[str] = []
    for label, query in SECTION_QUERIES:
        hits = retrieve_for_record(db, owner_id, record_id, query, top_k=4)
        section_notes.append(f"{label}: retrieved {len(hits)} passage(s)")
        for hit in hits:
            evidence_rows[hit.id] = hit

    evidence_items = _evidence_passages(db, list(evidence_rows.values()))
    allowed_ids = {item.id for item in evidence_items}
    user_prompt = build_user_prompt(
        [item.model_dump() for item in evidence_items],
        section_notes,
    )
    raw = provider.generate(SYSTEM_PROMPT, user_prompt)
    summary, warnings = _parse_and_validate(raw.text, allowed_ids, provider.is_mock)
    row = Summary(
        owner_id=owner_id,
        record_id=record.id,
        summary_json=summary.model_dump_json(),
        evidence_json=json.dumps([item.model_dump() for item in evidence_items]),
        prompt_version=PROMPT_VERSION,
        generation_provider=raw.provider,
        generation_model=raw.model_id,
        embedding_model=embedding.model_id,
        is_mock=raw.is_mock,
        validation_warnings_json=json.dumps(warnings),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row, summary, evidence_items, warnings)


def latest_summary(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> SummaryResponse:
    get_owned_record(db, record_id, owner_id)
    row = db.scalar(
        select(Summary)
        .where(Summary.owner_id == owner_id, Summary.record_id == record_id)
        .order_by(Summary.created_at.desc())
    )
    if row is None:
        raise AppError(status_code=404, detail="No summary has been generated for this record.")
    summary = StructuredSummary.model_validate_json(row.summary_json)
    evidence = [EvidencePassage.model_validate(item) for item in json.loads(row.evidence_json)]
    warnings = json.loads(row.validation_warnings_json)
    return _to_response(row, summary, evidence, warnings)


def _evidence_passages(db: Session, chunks: list[Chunk]) -> list[EvidencePassage]:
    if not chunks:
        return []
    document_ids = {chunk.document_id for chunk in chunks}
    documents = db.scalars(select(Document).where(Document.id.in_(document_ids))).all()
    names = {document.id: document.original_filename for document in documents}
    return [
        EvidencePassage(
            id=str(chunk.id),
            document_id=str(chunk.document_id),
            original_filename=names.get(chunk.document_id, "document"),
            page=chunk.source_page,
            method=chunk.extraction_method,
            text=chunk.text,
        )
        for chunk in chunks
    ]


def _parse_and_validate(text: str, allowed_ids: set[str], is_mock: bool) -> tuple[StructuredSummary, list[str]]:
    warnings: list[str] = []
    if is_mock:
        warnings.append("MOCK/TEST OUTPUT: this summary is not a real-model result.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        payload = json.loads(cleaned)
        summary = StructuredSummary.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AppError(status_code=502, detail="The model output was not valid structured JSON.") from exc

    for field_name in (
        "key_history",
        "current_documented_findings",
        "medications",
        "allergies",
        "laboratory_findings",
    ):
        claims: list[Claim] = getattr(summary, field_name)
        kept: list[Claim] = []
        for claim in claims:
            unknown = [item for item in claim.source_ids if item not in allowed_ids]
            if unknown:
                warnings.append(f"Removed unknown citation IDs from a {field_name} claim.")
                claim.source_ids = [item for item in claim.source_ids if item in allowed_ids]
            if claim.source_ids:
                claim.evidence_status = "citation_present"
                kept.append(claim)
            else:
                warnings.append("A claim had no valid citation and was moved to unresolved information.")
                summary.unresolved_or_unavailable.append(f"Uncited claim requiring review: {claim.text}")
        setattr(summary, field_name, kept)

    if not allowed_ids:
        warnings.append("No retrieved evidence was available; missing information is expected.")
        if "No evidence was supplied" not in " ".join(summary.unresolved_or_unavailable):
            summary.unresolved_or_unavailable.append("No retrieved evidence was available for this record.")
    return summary, warnings


def _to_response(
    row: Summary,
    summary: StructuredSummary,
    evidence: list[EvidencePassage],
    warnings: list[str],
) -> SummaryResponse:
    return SummaryResponse(
        id=row.id,
        record_id=row.record_id,
        summary=summary,
        evidence=evidence,
        prompt_version=row.prompt_version,
        generation_provider=row.generation_provider,
        generation_model=row.generation_model,
        embedding_model=row.embedding_model,
        is_mock=row.is_mock,
        validation_warnings=warnings,
        created_at=row.created_at,
    )
