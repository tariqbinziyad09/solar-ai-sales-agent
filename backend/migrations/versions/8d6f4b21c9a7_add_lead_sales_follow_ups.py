"""add lead sales follow ups

Revision ID: 8d6f4b21c9a7
Revises: 123f33be6f8b
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8d6f4b21c9a7"
down_revision: str | Sequence[str] | None = "123f33be6f8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("next_follow_up_at", sa.DateTime(), nullable=True))
    op.add_column("leads", sa.Column("follow_up_note", sa.String(length=500), nullable=True))
    op.add_column("leads", sa.Column("follow_up_completed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "follow_up_completed_at")
    op.drop_column("leads", "follow_up_note")
    op.drop_column("leads", "next_follow_up_at")
