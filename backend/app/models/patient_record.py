"""Synthetic patient-record container. No real-world identifiers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.document import Document


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PatientRecord(Base):
    """A container for documents belonging to one synthetic/de-identified case."""

    __tablename__ = "patient_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_label: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="records")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )
