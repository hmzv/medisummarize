"""Baseline schema for Segment 1.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-05

Segment 1 has no domain tables. This revision exists so
`alembic upgrade head` is a valid, empty no-op against a fresh database.
"""

from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
