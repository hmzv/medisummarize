"""Owner-scoped document upload and access."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.user import User
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.schemas.extraction import ExtractedPageListResponse, ExtractedPageResponse
from app.services.extraction import (
    extract_document,
    extract_document_job,
    extracted_payload,
    list_extracted_pages,
)
from app.services.ingestion import (
    delete_document,
    get_owned_document,
    list_documents,
    upload_document,
)
from app.services.ingestion.storage import document_path

router = APIRouter(prefix="/records/{record_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
) -> DocumentResponse:
    document = upload_document(db, current_user.id, record_id, file)
    if get_settings().extract_on_upload:
        background_tasks.add_task(extract_document_job, str(document.id))
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_record_documents(
    record_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentListResponse:
    items = list_documents(db, current_user.id, record_id)
    return DocumentListResponse(items=[DocumentResponse.model_validate(item) for item in items])


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    record_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentResponse:
    document = get_owned_document(db, current_user.id, record_id, document_id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/file")
def download_document(
    record_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    document = get_owned_document(db, current_user.id, record_id, document_id)
    path = document_path(get_settings(), document)
    if not path.is_file():
        raise AppError(status_code=404, detail="Document file is no longer available.")
    return FileResponse(
        path=path,
        media_type=document.detected_media_type,
        filename=document.original_filename,
        content_disposition_type="attachment",
    )


@router.post("/{document_id}/extract", response_model=ExtractedPageListResponse)
def run_extract(
    record_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ExtractedPageListResponse:
    document = get_owned_document(db, current_user.id, record_id, document_id)
    return extract_document(db, document.id)


@router.get("/{document_id}/extracted", response_model=ExtractedPageListResponse)
def get_extracted(
    record_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ExtractedPageListResponse:
    document = get_owned_document(db, current_user.id, record_id, document_id)
    pages = list_extracted_pages(db, current_user.id, record_id, document_id)
    return extracted_payload(document, pages)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    record_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    delete_document(db, current_user.id, record_id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
