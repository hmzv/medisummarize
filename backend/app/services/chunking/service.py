"""Page-aware, overlap-safe chunking with deterministic IDs."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from app.models.extracted_page import ExtractedPage

CHUNKING_VERSION = "chunk-v1"


@dataclass(frozen=True)
class TextChunk:
    chunk_id: uuid.UUID
    owner_id: uuid.UUID
    record_id: uuid.UUID
    document_id: uuid.UUID
    source_page: int
    start_char: int
    end_char: int
    text: str
    extraction_method: str
    ocr_confidence: float | None
    warnings: list[str]
    chunking_version: str
    document_date_text: str | None
    document_date_confidence: str | None


def chunk_extracted_pages(
    pages: list[ExtractedPage],
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size to avoid infinite loops")

    chunks: list[TextChunk] = []
    for page in pages:
        chunks.extend(_chunk_page(page, chunk_size, overlap))
    return chunks


def _chunk_page(page: ExtractedPage, chunk_size: int, overlap: int) -> list[TextChunk]:
    text = page.text or ""
    if not text.strip():
        return []
    warnings = _warnings(page)
    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end]
        if piece.strip():
            chunks.append(
                TextChunk(
                    chunk_id=_deterministic_id(page.document_id, page.page_number, start, end),
                    owner_id=page.owner_id,
                    record_id=page.record_id,
                    document_id=page.document_id,
                    source_page=page.page_number,
                    start_char=start,
                    end_char=end,
                    text=piece,
                    extraction_method=page.extraction_method,
                    ocr_confidence=page.ocr_confidence,
                    warnings=warnings,
                    chunking_version=CHUNKING_VERSION,
                    document_date_text=None,
                    document_date_confidence=None,
                )
            )
        if end >= length:
            break
        start += step
    return chunks


def _deterministic_id(document_id: uuid.UUID, page_number: int, start: int, end: int) -> uuid.UUID:
    material = f"{CHUNKING_VERSION}:{document_id}:{page_number}:{start}:{end}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return uuid.UUID(digest[:32])


def _warnings(page: ExtractedPage) -> list[str]:
    try:
        payload = json.loads(page.warnings_json or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload]
