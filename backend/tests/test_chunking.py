"""Chunking behaviour."""

from __future__ import annotations

import uuid

import pytest

from app.models.extracted_page import ExtractedPage
from app.services.chunking.service import chunk_extracted_pages


def _page(text: str, page_number: int = 1) -> ExtractedPage:
    return ExtractedPage(
        owner_id=uuid.uuid4(),
        record_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=page_number,
        text=text,
        extraction_method="utf8_text",
        warnings_json="[]",
    )


def test_empty_input_yields_no_chunks() -> None:
    assert chunk_extracted_pages([_page("   ")]) == []


def test_chunking_is_reproducible_and_keeps_provenance() -> None:
    page = _page("denied chest pain " * 20)
    first = chunk_extracted_pages([page], chunk_size=40, overlap=10)
    second = chunk_extracted_pages([page], chunk_size=40, overlap=10)
    assert first
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]
    assert all(item.source_page == 1 for item in first)
    assert all(item.document_id == page.document_id for item in first)
    assert all(item.owner_id == page.owner_id for item in first)


def test_overlap_smaller_than_size_is_required() -> None:
    page = _page("abcdef")
    with pytest.raises(ValueError, match="overlap"):
        chunk_extracted_pages([page], chunk_size=10, overlap=10)


def test_page_aware_chunking_does_not_merge_pages() -> None:
    pages = [_page("alpha " * 10, 1), _page("beta " * 10, 2)]
    chunks = chunk_extracted_pages(pages, chunk_size=40, overlap=5)
    assert {item.source_page for item in chunks} == {1, 2}
    assert all("beta" not in item.text or item.source_page == 2 for item in chunks)
