"""Document upload, validation, isolation, and protected download."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _auth(payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def _pdf_bytes(text: str = "SYNTHETIC — NOT A REAL PATIENT") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def _image_bytes(fmt: str = "PNG") -> bytes:
    image = Image.new("RGB", (64, 48), color=(240, 240, 240))
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def _create_record(client: TestClient, user: dict, label: str = "Case upload") -> str:
    response = client.post(
        "/api/v1/records",
        json={"display_label": label},
        headers=_auth(user),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_upload_pdf_png_jpeg_and_text(client: TestClient, register_user, tmp_path: Path) -> None:
    user = register_user("docs@example.com")
    record_id = _create_record(client, user)
    headers = _auth(user)

    pdf = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("lab-report.pdf", _pdf_bytes(), "application/octet-stream")},
    )
    assert pdf.status_code == 201, pdf.text
    body = pdf.json()
    assert body["file_kind"] == "pdf"
    assert body["status"] == "uploaded"
    assert body["page_count"] == 1
    assert body["original_filename"] == "lab-report.pdf"
    assert "stored_name" not in body
    assert str(tmp_path) not in pdf.text

    png = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("scan.png", _image_bytes("PNG"), "image/gif")},
    )
    assert png.status_code == 201, png.text
    assert png.json()["file_kind"] == "image"
    assert png.json()["image_width"] == 64

    jpeg = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("photo.jpg", _image_bytes("JPEG"))},
    )
    assert jpeg.status_code == 201, jpeg.text

    text = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("note.txt", "SYNTHETIC note\nGlucose 5.2 mmol/L\n".encode("utf-8"))},
    )
    assert text.status_code == 201, text.text
    assert text.json()["file_kind"] == "text"

    listed = client.get(f"/api/v1/records/{record_id}/documents", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 4


def test_rejects_mismatched_and_unsupported_types(client: TestClient, register_user, tmp_path: Path) -> None:
    user = register_user("badfile@example.com")
    record_id = _create_record(client, user)
    headers = _auth(user)

    mismatch = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("report.pdf", _image_bytes("PNG"))},
    )
    assert mismatch.status_code == 415
    assert str(tmp_path) not in mismatch.text
    assert "uploads" not in mismatch.json()["detail"]

    exe = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("payload.exe", _pdf_bytes())},
    )
    assert exe.status_code == 415

    binary_as_text = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("note.txt", b"\x00\x01\x02\x03")},
    )
    assert binary_as_text.status_code == 415


def test_rejects_oversize_file(
    client: TestClient,
    register_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "64")
    from app.core.config import clear_settings_cache

    clear_settings_cache()
    user = register_user("oversize@example.com")
    record_id = _create_record(client, user)
    response = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=_auth(user),
        files={"file": ("note.txt", b"x" * 128)},
    )
    assert response.status_code == 413


def test_file_access_is_owner_scoped(client: TestClient, register_user) -> None:
    alice = register_user("alice-docs@example.com")
    bob = register_user("bob-docs@example.com")
    record_id = _create_record(client, alice)
    uploaded = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=_auth(alice),
        files={"file": ("note.txt", b"alice secret synthetic note")},
    )
    document_id = uploaded.json()["id"]

    bob_list = client.get(f"/api/v1/records/{record_id}/documents", headers=_auth(bob))
    assert bob_list.status_code == 404

    bob_get = client.get(
        f"/api/v1/records/{record_id}/documents/{document_id}",
        headers=_auth(bob),
    )
    assert bob_get.status_code == 404

    bob_file = client.get(
        f"/api/v1/records/{record_id}/documents/{document_id}/file",
        headers=_auth(bob),
    )
    assert bob_file.status_code == 404
    assert b"alice secret" not in bob_file.content

    alice_file = client.get(
        f"/api/v1/records/{record_id}/documents/{document_id}/file",
        headers=_auth(alice),
    )
    assert alice_file.status_code == 200
    assert alice_file.content == b"alice secret synthetic note"


def test_unauthenticated_upload_rejected(client: TestClient, register_user) -> None:
    user = register_user("noauth-docs@example.com")
    record_id = _create_record(client, user)
    response = client.post(
        f"/api/v1/records/{record_id}/documents",
        files={"file": ("note.txt", b"hello")},
    )
    assert response.status_code == 401


def test_delete_removes_file_and_listing(client: TestClient, register_user) -> None:
    user = register_user("delete-docs@example.com")
    record_id = _create_record(client, user)
    headers = _auth(user)
    uploaded = client.post(
        f"/api/v1/records/{record_id}/documents",
        headers=headers,
        files={"file": ("note.txt", b"to be deleted")},
    )
    document_id = uploaded.json()["id"]
    deleted = client.delete(
        f"/api/v1/records/{record_id}/documents/{document_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    missing = client.get(
        f"/api/v1/records/{record_id}/documents/{document_id}",
        headers=headers,
    )
    assert missing.status_code == 404
    listed = client.get(f"/api/v1/records/{record_id}/documents", headers=headers)
    assert listed.json()["items"] == []


def test_unknown_document_is_not_found(client: TestClient, register_user) -> None:
    user = register_user("unknown-doc@example.com")
    record_id = _create_record(client, user)
    response = client.get(
        f"/api/v1/records/{record_id}/documents/{uuid4()}",
        headers=_auth(user),
    )
    assert response.status_code == 404
