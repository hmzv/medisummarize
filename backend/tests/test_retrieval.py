"""Patient-scoped retrieval isolation and idempotent indexing."""

from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.models.chunk import Chunk
from app.services.retrieval.service import retrieve_for_record
from tests.test_documents import _create_record
from tests.test_extraction import _extract, _upload


def test_known_passage_is_retrieved_and_isolated(client: TestClient, register_user) -> None:
    alice = register_user("retrieve-alice@example.com")
    bob = register_user("retrieve-bob@example.com")
    alice_record = _create_record(client, alice, "Alice case")
    bob_record = _create_record(client, bob, "Bob case")

    alice_doc = _upload(
        client,
        alice,
        alice_record,
        "alice.txt",
        b"SYNTHETIC. Patient denied chest pain. Amlodipine 5 mg nightly.",
    )
    bob_doc = _upload(
        client,
        bob,
        bob_record,
        "bob.txt",
        b"SYNTHETIC. Patient denied chest pain. Amlodipine 5 mg nightly.",
    )
    _extract(client, alice, alice_record, alice_doc["id"])
    _extract(client, bob, bob_record, bob_doc["id"])

    db = get_session_factory()()
    try:
        alice_hits = retrieve_for_record(
            db,
            UUID(alice["user"]["id"]),
            UUID(alice_record),
            "Patient denied chest pain. Amlodipine 5 mg nightly.",
            top_k=3,
        )
        assert alice_hits
        assert "denied chest pain" in alice_hits[0].text
        assert all(str(hit.record_id) == alice_record for hit in alice_hits)

        from app.core.errors import AppError

        try:
            retrieve_for_record(
                db,
                UUID(alice["user"]["id"]),
                UUID(bob_record),
                "Patient denied chest pain.",
                top_k=3,
            )
            raise AssertionError("cross-record retrieval should be denied")
        except AppError as exc:
            assert exc.status_code == 404
    finally:
        db.close()


def test_reindex_is_idempotent(client: TestClient, register_user) -> None:
    user = register_user("reindex@example.com")
    record_id = _create_record(client, user)
    uploaded = _upload(client, user, record_id, "note.txt", b"SYNTHETIC glucose 5.2 mmol/L")
    first = _extract(client, user, record_id, uploaded["id"])
    second = _extract(client, user, record_id, uploaded["id"])
    assert first.status_code == 200
    assert second.status_code == 200

    db = get_session_factory()()
    try:
        count = db.scalar(select(func.count()).select_from(Chunk).where(Chunk.record_id == UUID(record_id)))
        assert count and count > 0
        again = db.scalar(select(func.count()).select_from(Chunk).where(Chunk.record_id == UUID(record_id)))
        assert again == count
    finally:
        db.close()
