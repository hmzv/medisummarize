"""Owner-scoped synthetic patient-record containers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.records import RecordCreateRequest, RecordListResponse, RecordResponse
from app.services import records as record_service

router = APIRouter(prefix="/records", tags=["records"])


@router.post("", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: RecordCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecordResponse:
    record = record_service.create_record(db, current_user.id, payload.display_label)
    return RecordResponse.model_validate(record)


@router.get("", response_model=RecordListResponse)
def list_records(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecordListResponse:
    items = record_service.list_records_for_owner(db, current_user.id)
    return RecordListResponse(items=[RecordResponse.model_validate(item) for item in items])


@router.get("/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecordResponse:
    record = record_service.get_owned_record(db, record_id, current_user.id)
    return RecordResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    record_service.delete_owned_record(db, record_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
