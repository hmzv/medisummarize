"""Upload, list, download, and delete owner-scoped documents."""

from __future__ import annotations

import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.document import Document, DocumentStatus
from app.services.ingestion import storage as disk
from app.services.ingestion.validation import display_filename, validate_saved_file
from app.services.records import get_owned_record


def list_documents(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> list[Document]:
    get_owned_record(db, record_id, owner_id)
    statement = (
        select(Document)
        .where(
            Document.owner_id == owner_id,
            Document.record_id == record_id,
            Document.status != DocumentStatus.deleted.value,
        )
        .order_by(Document.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_owned_document(
    db: Session,
    owner_id: uuid.UUID,
    record_id: uuid.UUID,
    document_id: uuid.UUID,
) -> Document:
    get_owned_record(db, record_id, owner_id)
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
            Document.record_id == record_id,
            Document.status != DocumentStatus.deleted.value,
        )
    )
    if document is None:
        raise AppError(status_code=404, detail="Document not found.")
    return document


def upload_document(
    db: Session,
    owner_id: uuid.UUID,
    record_id: uuid.UUID,
    upload: UploadFile,
) -> Document:
    get_owned_record(db, owner_id=owner_id, record_id=record_id)
    settings = get_settings()
    original = display_filename(upload.filename)
    document_id = uuid.uuid4()
    temp_name = f".{document_id}.part"
    folder = disk.record_dir(settings, owner_id, record_id)
    temp_path = folder / temp_name
    size, digest = disk.write_upload_to_temp(upload, temp_path, settings.max_upload_bytes)
    try:
        detected = validate_saved_file(temp_path, original, size, settings)
        stored_name = f"{document_id}{detected.stored_suffix}"
        final_path = folder / stored_name
        temp_path.replace(final_path)
    except Exception:
        disk.delete_quiet(temp_path)
        raise

    document = Document(
        id=document_id,
        owner_id=owner_id,
        record_id=record_id,
        original_filename=original,
        stored_name=stored_name,
        file_kind=detected.kind.value,
        detected_media_type=detected.media_type,
        size_bytes=size,
        sha256=digest,
        status=DocumentStatus.uploaded.value,
        page_count=detected.page_count,
        image_width=detected.image_width,
        image_height=detected.image_height,
    )
    db.add(document)
    from app.services.summary_lifecycle import invalidate_summaries
    invalidate_summaries(db, owner_id, record_id)
    db.commit()
    db.refresh(document)
    return document


def delete_document(
    db: Session,
    owner_id: uuid.UUID,
    record_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    document = get_owned_document(db, owner_id, record_id, document_id)
    settings = get_settings()
    path = disk.document_path(settings, document)
    disk.delete_quiet(path)
    document.status = DocumentStatus.deleted.value
    from app.services.summary_lifecycle import invalidate_summaries
    from app.models.extracted_page import ExtractedPage
    from app.models.chunk import Chunk
    from sqlalchemy import delete
    invalidate_summaries(db, owner_id, record_id)
    db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    db.execute(delete(ExtractedPage).where(ExtractedPage.document_id == document_id))
    db.commit()
    # Rebuild rankings as well as rows: stale top-k IDs could otherwise hide
    # surviving passages, and deleted-source vectors must not remain on disk.
    from app.services.retrieval.service import index_owned_record
    index_owned_record(db, owner_id, record_id)


def delete_files_for_record(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> None:
    settings = get_settings()
    documents = db.scalars(
        select(Document).where(Document.owner_id == owner_id, Document.record_id == record_id)
    ).all()
    for document in documents:
        disk.delete_quiet(disk.document_path(settings, document))
