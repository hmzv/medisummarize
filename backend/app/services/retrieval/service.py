"""Authorize-then-search retrieval over a single patient-record index."""

from __future__ import annotations

import json
import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.extracted_page import ExtractedPage
from app.services.chunking.service import chunk_extracted_pages
from app.services.embeddings.providers import get_embedding_provider
from app.services.records import get_owned_record
from app.services.retrieval.index_store import delete_record_index, search_record_index, write_record_index
from app.services.record_lock import record_write_lock


def index_owned_record(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> int:
    with record_write_lock(record_id):
        return _index_owned_record(db, owner_id, record_id)


def _index_owned_record(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> int:
    get_owned_record(db, record_id, owner_id)
    settings = get_settings()
    provider = get_embedding_provider()
    pages = list(
        db.scalars(
            select(ExtractedPage).where(
                ExtractedPage.owner_id == owner_id,
                ExtractedPage.record_id == record_id,
            )
        ).all()
    )
    built = chunk_extracted_pages(pages, settings.chunk_size, settings.chunk_overlap)
    existing = db.scalars(
        select(Chunk).where(Chunk.owner_id == owner_id, Chunk.record_id == record_id)
    ).all()
    for row in existing:
        db.delete(row)
    db.flush()

    chunk_ids: list[uuid.UUID] = []
    texts: list[str] = []
    for item in built:
        db.add(
            Chunk(
                id=item.chunk_id,
                owner_id=item.owner_id,
                record_id=item.record_id,
                document_id=item.document_id,
                source_page=item.source_page,
                start_char=item.start_char,
                end_char=item.end_char,
                text=item.text,
                extraction_method=item.extraction_method,
                ocr_confidence=item.ocr_confidence,
                warnings_json=json.dumps(item.warnings),
                chunking_version=item.chunking_version,
                embedding_model=provider.model_id,
                document_date_text=item.document_date_text,
                document_date_confidence=item.document_date_confidence,
            )
        )
        chunk_ids.append(item.chunk_id)
        texts.append(item.text)
    db.commit()

    if not texts:
        delete_record_index(record_id)
        _mark_documents(db, owner_id, record_id, DocumentStatus.extracted.value)
        return 0

    vectors = np.asarray(provider.embed(texts), dtype=np.float32)
    write_record_index(record_id, chunk_ids, vectors, provider)
    _mark_documents(db, owner_id, record_id, DocumentStatus.indexed.value)
    return len(chunk_ids)


def retrieve_for_record(
    db: Session,
    owner_id: uuid.UUID,
    record_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
) -> list[Chunk]:
    get_owned_record(db, record_id, owner_id)
    provider = get_embedding_provider()
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    query_vector = provider.embed([query])[0]
    ranked = search_record_index(record_id, query_vector, k, provider.model_id, provider.dimension)
    if not ranked:
        return []
    ids = [chunk_id for chunk_id, _score in ranked]
    rows = db.scalars(select(Chunk).where(Chunk.id.in_(ids), Chunk.owner_id == owner_id, Chunk.record_id == record_id)).all()
    by_id = {row.id: row for row in rows}
    return [by_id[chunk_id] for chunk_id, _score in ranked if chunk_id in by_id]


def _mark_documents(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID, status: str) -> None:
    documents = db.scalars(
        select(Document).where(
            Document.owner_id == owner_id,
            Document.record_id == record_id,
            Document.status.in_(
                [
                    DocumentStatus.extracted.value,
                    DocumentStatus.indexed.value,
                    DocumentStatus.ready.value,
                ]
            ),
        )
    ).all()
    for document in documents:
        document.status = status
    db.commit()
