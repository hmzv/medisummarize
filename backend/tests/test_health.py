"""Smoke tests for liveness, readiness, and CORS."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "medisummarize-ai"
    assert body["environment"] == "test"


def test_ready_checks_database(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "connected"


def test_root_includes_disclaimer(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "Not for diagnosis" in body["disclaimer"]
    assert body["health"] == "/api/v1/health"


def test_cors_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_does_not_reflect_unknown_origin(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "https://evil.example"


def test_generation_health_labels_mock_provider(client: TestClient) -> None:
    response = client.get("/api/v1/health/generation")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["is_mock"] is True
    assert "MOCK/TEST OUTPUT" in body["warning"]
