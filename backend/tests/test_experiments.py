"""Experiment imports must not create false scores or cross user boundaries."""
import copy
import json


def payload():
    return {"schema_version": 1, "runs": [{
        "schema_version": 1, "task": "handwriting_word_ocr", "model": "Tesseract", "dataset": "Test fixture",
        "dataset_sha256": "a" * 64, "split": "validation", "samples": 2,
        "metrics": {"samples": 2, "cer": 1.2, "wer": 0.5, "exact_match": 0.5},
        "elapsed_seconds": 1, "created_at": "2026-11-10T00:00:00Z", "is_mock": False,
        "provenance": {"fixture": True}, "limitations": ["Test fixture only"]
    }]}


def headers(user): return {"Authorization": f"Bearer {user['access_token']}"}


def test_import_is_owner_scoped_and_idempotent(client, register_user):
    alice, bob = register_user("alice-exp@example.com"), register_user("bob-exp@example.com")
    for _ in range(2):
        response = client.post("/api/v1/experiments/import", json=payload(), headers=headers(alice))
        assert response.status_code == 201, response.text
        assert response.json()["items"][0]["verification"] == "user_supplied"
    assert len(client.get("/api/v1/experiments", headers=headers(alice)).json()["items"]) == 1
    assert client.get("/api/v1/experiments", headers=headers(bob)).json()["items"] == []
    assert client.get("/api/v1/experiments").status_code == 401


def test_mock_nan_and_inconsistent_counts_rejected(client, register_user):
    auth = headers(register_user("invalid-exp@example.com"))
    for field, value in [("is_mock", True), ("samples", 3)]:
        data = copy.deepcopy(payload()); data["runs"][0][field] = value
        assert client.post("/api/v1/experiments/import", json=data, headers=auth).status_code == 422
    data = payload(); data["runs"][0]["metrics"]["cer"] = float("nan")
    raw = json.dumps(data)
    assert client.post("/api/v1/experiments/import", content=raw, headers=auth).status_code == 422
    assert client.post("/api/v1/experiments/import", content="x" * 1_000_001, headers=auth).status_code == 413
