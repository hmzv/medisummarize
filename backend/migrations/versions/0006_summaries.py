"""Summaries table.

Revision ID: 0006_summaries
Revises: 0005_chunks
Create Date: 2026-10-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_summaries"
down_revision: Union[str, Sequence[str], None] = "0005_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("generation_provider", sa.String(length=40), nullable=False),
        sa.Column("generation_model", sa.String(length=120), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.Column("validation_warnings_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["patient_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_summaries_owner_id", "summaries", ["owner_id"])
    op.create_index("ix_summaries_record_id", "summaries", ["record_id"])


def downgrade() -> None:
    op.drop_index("ix_summaries_record_id", table_name="summaries")
    op.drop_index("ix_summaries_owner_id", table_name="summaries")
    op.drop_table("summaries")
