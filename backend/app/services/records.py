"""Owner-scoped patient-record containers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.patient_record import PatientRecord


def create_record(db: Session, owner_id: UUID, display_label: str) -> PatientRecord:
    record = PatientRecord(owner_id=owner_id, display_label=display_label.strip())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_records_for_owner(db: Session, owner_id: UUID) -> list[PatientRecord]:
    statement = (
        select(PatientRecord)
        .where(PatientRecord.owner_id == owner_id)
        .order_by(PatientRecord.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_owned_record(db: Session, record_id: UUID, owner_id: UUID) -> PatientRecord:
    record = db.scalar(
        select(PatientRecord).where(
            PatientRecord.id == record_id,
            PatientRecord.owner_id == owner_id,
        )
    )
    if record is None:
        raise AppError(status_code=404, detail="Record not found.")
    return record


def delete_owned_record(db: Session, record_id: UUID, owner_id: UUID) -> None:
    record = get_owned_record(db, record_id, owner_id)
    from app.services.ingestion.service import delete_files_for_record

    delete_files_for_record(db, owner_id, record_id)
    db.delete(record)
    db.commit()
