"""Extraction and OCR tests using synthetic fixtures."""

from __future__ import annotations

from io import BytesIO
from shutil import which

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from tests.test_documents import _auth, _create_record, _pdf_bytes


def _upload(client: TestClient, user: dict, record_id: str, filename: str, data: bytes) -> dict:
    response = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=_auth(user),
        files={"file": (filename, data)},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _extract(client: TestClient, user: dict, record_id: str, document_id: str):
    return client.post(
        f"/api/v1/records/{record_id}/documents/{document_id}/extract",
        headers=_auth(user),
    )


def test_text_pdf_extraction(client: TestClient, register_user) -> None:
    user = register_user("extract-pdf@example.com")
    record_id = _create_record(client, user)
    uploaded = _upload(
        client,
        user,
        record_id,
        "note.pdf",
        _pdf_bytes("SYNTHETIC — denied chest pain. Amlodipine 5 mg nightly."),
    )
    response = _extract(client, user, record_id, uploaded["id"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {"extracted", "indexed", "ready"}
    assert body["items"][0]["extraction_method"] == "pdf_text"
    assert "denied chest pain" in body["items"][0]["text"]
    assert "Amlodipine 5 mg" in body["items"][0]["text"]
    assert body["items"][0]["page_number"] == 1


def test_utf8_text_extraction(client: TestClient, register_user) -> None:
    user = register_user("extract-text@example.com")
    record_id = _create_record(client, user)
    uploaded = _upload(
        client,
        user,
        record_id,
        "labs.txt",
        "SYNTHETIC — NOT A REAL PATIENT\r\nGlucose 5.2 mmol/L\n".encode("utf-8"),
    )
    response = _extract(client, user, record_id, uploaded["id"])
    assert response.status_code == 200
    page = response.json()["items"][0]
    assert page["extraction_method"] == "utf8_text"
    assert "Glucose 5.2 mmol/L" in page["text"]
    assert "\r" not in page["text"]


def test_empty_text_extraction_is_understandable(client: TestClient, register_user) -> None:
    user = register_user("extract-empty@example.com")
    record_id = _create_record(client, user)
    uploaded = _upload(client, user, record_id, "empty.txt", b"   \n")
    response = _extract(client, user, record_id, uploaded["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["public_error"]


def test_extracted_text_is_owner_scoped(client: TestClient, register_user) -> None:
    alice = register_user("extract-alice@example.com")
    bob = register_user("extract-bob@example.com")
    record_id = _create_record(client, alice)
    uploaded = _upload(client, alice, record_id, "note.txt", b"alice only synthetic text")
    _extract(client, alice, record_id, uploaded["id"])
    bob_view = client.get(
        f"/api/v1/records/{record_id}/documents/{uploaded['id']}/extracted",
        headers=_auth(bob),
    )
    assert bob_view.status_code == 404


@pytest.mark.skipif(which("tesseract") is None, reason="Tesseract OCR is not on PATH")
def test_image_ocr_and_mixed_pdf(client: TestClient, register_user) -> None:
    user = register_user("extract-ocr@example.com")
    record_id = _create_record(client, user)
    image = _text_image("SYNTHETIC GLUCOSE")
    uploaded = _upload(client, user, record_id, "scan.png", image)
    ocr = _extract(client, user, record_id, uploaded["id"])
    assert ocr.status_code == 200, ocr.text
    page = ocr.json()["items"][0]
    assert page["extraction_method"] == "ocr"
    assert page["warnings"]
    assert "GLUCOSE" in page["text"].upper()

    mixed = _mixed_pdf()
    mixed_doc = _upload(client, user, record_id, "mixed.pdf", mixed)
    mixed_extract = _extract(client, user, record_id, mixed_doc["id"])
    assert mixed_extract.status_code == 200, mixed_extract.text
    items = mixed_extract.json()["items"]
    assert len(items) == 2
    assert items[0]["extraction_method"] == "pdf_text"
    assert "denied chest pain" in items[0]["text"]
    assert items[1]["extraction_method"] == "ocr"


def _text_image(message: str) -> bytes:
    image = Image.new("RGB", (800, 200), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 70), message, fill="black", font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _mixed_pdf() -> bytes:
    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "SYNTHETIC discharge: denied chest pain. See scanned medication list.")
    second = document.new_page()
    image_bytes = _text_image("Amlodipine 5 mg")
    rectangle = fitz.Rect(40, 40, 560, 220)
    second.insert_image(rectangle, stream=image_bytes)
    data = document.tobytes()
    document.close()
    return data
