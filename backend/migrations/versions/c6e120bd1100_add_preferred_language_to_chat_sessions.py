"""add preferred language to chat sessions

Revision ID: YOUR_NEW_REVISION
Revises: 37038d736e5b
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c6e120bd1100"
down_revision: str | Sequence[str] | None = "37038d736e5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add preferred conversation language to chat sessions."""

    op.add_column(
        "chat_sessions",
        sa.Column(
            "preferred_language",
            sa.String(length=20),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove preferred conversation language from chat sessions."""

    op.drop_column(
        "chat_sessions",
        "preferred_language",
    )
