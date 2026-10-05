"""Chunk table.

Revision ID: 0005_chunks
Revises: 0004_extracted_pages
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_chunks"
down_revision: Union[str, Sequence[str], None] = "0004_extracted_pages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(length=40), nullable=False),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("chunking_version", sa.String(length=40), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("document_date_text", sa.String(length=80), nullable=True),
        sa.Column("document_date_confidence", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["patient_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_owner_id", "chunks", ["owner_id"])
    op.create_index("ix_chunks_record_id", "chunks", ["record_id"])


def downgrade() -> None:
    op.drop_index("ix_chunks_record_id", table_name="chunks")
    op.drop_index("ix_chunks_owner_id", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")
