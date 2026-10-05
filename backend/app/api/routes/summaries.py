"""Summary generation endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.summaries import SummaryResponse
from app.services.summarization import generate_record_summary, latest_summary

router = APIRouter(prefix="/records/{record_id}/summary", tags=["summaries"])


@router.post("", response_model=SummaryResponse, status_code=status.HTTP_201_CREATED)
def create_summary(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SummaryResponse:
    return generate_record_summary(db, current_user.id, record_id)


@router.get("", response_model=SummaryResponse)
def get_summary(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SummaryResponse:
    return latest_summary(db, current_user.id, record_id)
