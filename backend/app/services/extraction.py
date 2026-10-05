"""Page-aware extraction. Does not silently correct clinical strings."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.document import Document, DocumentStatus, FileKind
from app.models.extracted_page import ExtractedPage
from app.schemas.extraction import ExtractedPageListResponse, ExtractedPageResponse
from app.services.ingestion.storage import document_path
from app.services.ocr.engine import ocr_image, ocr_png_bytes

MIN_PDF_TEXT_CHARS = 40


@dataclass(frozen=True)
class PageExtraction:
    page_number: int
    text: str
    extraction_method: str
    ocr_confidence: float | None
    warnings: list[str]


def extract_document(db: Session, document_id: uuid.UUID) -> ExtractedPageListResponse:
    document = db.get(Document, document_id)
    if document is None or document.status == DocumentStatus.deleted.value:
        raise AppError(status_code=404, detail="Document not found.")
    document.status = DocumentStatus.processing.value
    document.public_error = None
    db.commit()
    try:
        pages = _extract_pages(document)
        _replace_pages(db, document, pages)
        if not any(page.text.strip() for page in pages):
            document.status = DocumentStatus.failed.value
            document.public_error = "No extractable text was found."
        else:
            document.status = DocumentStatus.extracted.value
        db.commit()
        if document.status == DocumentStatus.extracted.value:
            from app.services.retrieval.service import index_owned_record

            index_owned_record(db, document.owner_id, document.record_id)
            db.refresh(document)
    except AppError as exc:
        document.status = DocumentStatus.failed.value
        document.public_error = exc.detail
        db.commit()
        raise
    except Exception:
        document.status = DocumentStatus.failed.value
        document.public_error = "Extraction failed."
        db.commit()
        raise AppError(status_code=400, detail="Extraction failed.") from None
    db.refresh(document)
    return extracted_payload(document, list_extracted_pages(db, document.owner_id, document.record_id, document.id))


def list_extracted_pages(
    db: Session,
    owner_id: uuid.UUID,
    record_id: uuid.UUID,
    document_id: uuid.UUID,
) -> list[ExtractedPage]:
    statement = (
        select(ExtractedPage)
        .where(
            ExtractedPage.owner_id == owner_id,
            ExtractedPage.record_id == record_id,
            ExtractedPage.document_id == document_id,
        )
        .order_by(ExtractedPage.page_number.asc())
    )
    return list(db.scalars(statement).all())


def extracted_payload(document: Document, pages: list[ExtractedPage]) -> ExtractedPageListResponse:
    return ExtractedPageListResponse(
        document_id=document.id,
        status=document.status,
        public_error=document.public_error,
        items=[_page_response(page) for page in pages],
    )


def _page_response(page: ExtractedPage) -> ExtractedPageResponse:
    try:
        warnings = json.loads(page.warnings_json or "[]")
    except json.JSONDecodeError:
        warnings = ["Extraction warnings could not be parsed."]
    if not isinstance(warnings, list):
        warnings = []
    return ExtractedPageResponse(
        id=page.id,
        document_id=page.document_id,
        page_number=page.page_number,
        text=page.text,
        extraction_method=page.extraction_method,
        ocr_confidence=page.ocr_confidence,
        warnings=[str(item) for item in warnings],
        created_at=page.created_at,
    )


def extract_document_job(document_id: str) -> None:
    """In-process background job. Not durable across process restarts."""
    from app.db.session import get_session_factory

    db = get_session_factory()()
    try:
        extract_document(db, uuid.UUID(document_id))
    except AppError:
        pass
    finally:
        db.close()


def _extract_pages(document: Document) -> list[PageExtraction]:
    settings = get_settings()
    path = document_path(settings, document)
    if not path.is_file():
        raise AppError(status_code=404, detail="Document file is no longer available.")
    if document.file_kind == FileKind.text.value:
        return [_extract_text_file(path.read_bytes())]
    if document.file_kind == FileKind.image.value:
        with Image.open(path) as image:
            text, confidence, warnings = ocr_image(image.convert("RGB"))
        return [
            PageExtraction(
                page_number=1,
                text=text,
                extraction_method="ocr",
                ocr_confidence=confidence,
                warnings=warnings,
            )
        ]
    if document.file_kind == FileKind.pdf.value:
        return _extract_pdf(path)
    raise AppError(status_code=400, detail="Unsupported file kind for extraction.")


def _extract_text_file(raw: bytes) -> PageExtraction:
    warnings: list[str] = []
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        warnings.append("The text file is empty.")
    return PageExtraction(
        page_number=1,
        text=text,
        extraction_method="utf8_text",
        ocr_confidence=None,
        warnings=warnings,
    )


def _extract_pdf(path) -> list[PageExtraction]:
    import fitz

    pages: list[PageExtraction] = []
    with fitz.open(path) as pdf:
        for index, page in enumerate(pdf, start=1):
            native = page.get_text("text") or ""
            native = native.replace("\r\n", "\n").replace("\r", "\n")
            if len(native.strip()) >= MIN_PDF_TEXT_CHARS:
                pages.append(
                    PageExtraction(
                        page_number=index,
                        text=native,
                        extraction_method="pdf_text",
                        ocr_confidence=None,
                        warnings=[],
                    )
                )
                continue
            pixmap = page.get_pixmap(dpi=200)
            png_bytes = pixmap.tobytes("png")
            text, confidence, warnings = ocr_png_bytes(png_bytes)
            if native.strip():
                warnings = [
                    "Native PDF text was sparse; OCR was applied. Sparse native text was not merged.",
                    *warnings,
                ]
            pages.append(
                PageExtraction(
                    page_number=index,
                    text=text,
                    extraction_method="ocr",
                    ocr_confidence=confidence,
                    warnings=warnings,
                )
            )
    return pages


def _replace_pages(db: Session, document: Document, pages: list[PageExtraction]) -> None:
    existing = db.scalars(select(ExtractedPage).where(ExtractedPage.document_id == document.id)).all()
    for row in existing:
        db.delete(row)
    db.flush()
    for page in pages:
        db.add(
            ExtractedPage(
                owner_id=document.owner_id,
                record_id=document.record_id,
                document_id=document.id,
                page_number=page.page_number,
                text=page.text,
                extraction_method=page.extraction_method,
                ocr_confidence=page.ocr_confidence,
                warnings_json=json.dumps(page.warnings),
            )
        )
