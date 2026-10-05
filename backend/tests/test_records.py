"""Ownership isolation for synthetic patient-record containers."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient


def _auth_header(payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_create_list_view_delete_own_record(client: TestClient, register_user) -> None:
    user = register_user("owner@example.com")
    headers = _auth_header(user)

    created = client.post(
        "/api/v1/records",
        json={"display_label": "Case A — synthetic longitudinal demo"},
        headers=headers,
    )
    assert created.status_code == 201
    record = created.json()
    assert record["display_label"] == "Case A — synthetic longitudinal demo"
    assert "SYNTHETIC" in record["synthetic_notice"]
    assert "owner_id" not in record

    listed = client.get("/api/v1/records", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    viewed = client.get(f"/api/v1/records/{record['id']}", headers=headers)
    assert viewed.status_code == 200
    assert viewed.json()["id"] == record["id"]

    deleted = client.delete(f"/api/v1/records/{record['id']}", headers=headers)
    assert deleted.status_code == 204
    missing = client.get(f"/api/v1/records/{record['id']}", headers=headers)
    assert missing.status_code == 404


def test_user_cannot_access_another_users_record(client: TestClient, register_user) -> None:
    alice = register_user("alice@example.com")
    bob = register_user("bob@example.com")
    created = client.post(
        "/api/v1/records",
        json={"display_label": "Alice synthetic case"},
        headers=_auth_header(alice),
    )
    record_id = created.json()["id"]

    bob_get = client.get(f"/api/v1/records/{record_id}", headers=_auth_header(bob))
    assert bob_get.status_code == 404

    bob_delete = client.delete(f"/api/v1/records/{record_id}", headers=_auth_header(bob))
    assert bob_delete.status_code == 404

    bob_list = client.get("/api/v1/records", headers=_auth_header(bob))
    assert bob_list.json()["items"] == []

    alice_get = client.get(f"/api/v1/records/{record_id}", headers=_auth_header(alice))
    assert alice_get.status_code == 200


def test_unauthenticated_record_access_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/records")
    assert response.status_code == 401
    created = client.post("/api/v1/records", json={"display_label": "No auth"})
    assert created.status_code == 401


def test_client_cannot_supply_owner_id(client: TestClient, register_user) -> None:
    user = register_user("no-spoof@example.com")
    response = client.post(
        "/api/v1/records",
        json={"display_label": "Spoof attempt", "owner_id": str(uuid4())},
        headers=_auth_header(user),
    )
    assert response.status_code == 422


def test_unknown_record_id_is_not_found(client: TestClient, register_user) -> None:
    user = register_user("unknown-record@example.com")
    response = client.get(f"/api/v1/records/{uuid4()}", headers=_auth_header(user))
    assert response.status_code == 404
