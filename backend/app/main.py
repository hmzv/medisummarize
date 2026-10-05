"""FastAPI application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.records import router as records_router
from app.api.routes.summaries import router as summaries_router
from app.core.config import get_settings
from app.core.errors import AppError

DISCLAIMER = (
    "Research prototype for clinical-document summarization only. "
    "Not for diagnosis, prescribing, treatment recommendations, or autonomous "
    "clinical decision-making. Verify all generated information against the "
    "original records."
)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="FYP-I research prototype. Not a clinical decision-support product.",
        description=DISCLAIMER,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(auth_router, prefix=settings.api_prefix)
    application.include_router(records_router, prefix=settings.api_prefix)
    application.include_router(documents_router, prefix=settings.api_prefix)
    application.include_router(summaries_router, prefix=settings.api_prefix)

    @application.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
            "disclaimer": DISCLAIMER,
        }

    return application


app = create_app()
