"""Extracted pages table.

Revision ID: 0004_extracted_pages
Revises: 0003_documents
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_extracted_pages"
down_revision: Union[str, Sequence[str], None] = "0003_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extracted_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(length=40), nullable=False),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["patient_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_extracted_pages_document_id", "extracted_pages", ["document_id"])
    op.create_index("ix_extracted_pages_owner_id", "extracted_pages", ["owner_id"])
    op.create_index("ix_extracted_pages_record_id", "extracted_pages", ["record_id"])


def downgrade() -> None:
    op.drop_index("ix_extracted_pages_record_id", table_name="extracted_pages")
    op.drop_index("ix_extracted_pages_owner_id", table_name="extracted_pages")
    op.drop_index("ix_extracted_pages_document_id", table_name="extracted_pages")
    op.drop_table("extracted_pages")
