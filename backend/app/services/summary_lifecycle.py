"""Invalidate stored source snapshots whenever a record's documents change."""
import uuid
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.models.summary import Summary


def invalidate_summaries(db: Session, owner_id: uuid.UUID, record_id: uuid.UUID) -> None:
    db.execute(delete(Summary).where(Summary.owner_id == owner_id, Summary.record_id == record_id))
