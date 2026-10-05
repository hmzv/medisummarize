"""Liveness and readiness endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.schemas.health import GenerationHealthResponse, HealthResponse, ReadyResponse
from app.services.generation.providers import get_generation_provider

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Process liveness. Does not query the database."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="medisummarize-ai",
        environment=settings.environment,
    )


@router.get("/health/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)) -> ReadyResponse:
    """Readiness: application plus database connectivity."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable.",
        ) from None
    return ReadyResponse(status="ready", database="connected")


@router.get("/health/generation", response_model=GenerationHealthResponse)
def generation_health() -> GenerationHealthResponse:
    """Observable generation-provider status. Mock mode is never silent."""
    provider = get_generation_provider()
    payload = provider.health()
    warning = payload.get("warning")
    if provider.is_mock:
        warning = "MOCK/TEST OUTPUT is enabled. Do not treat generated text as a real-model result."
    return GenerationHealthResponse(
        status=payload.get("status", "unknown"),
        provider=provider.provider_name,
        is_mock=provider.is_mock,
        warning=warning,
    )
