"""add lead foreign key to chat sessions

Revision ID: d4bf4810d670
Revises: 2ed4543ad46f
Create Date: 2026-09-28 00:52:25.561133

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4bf4810d670"
down_revision: str | Sequence[str] | None = "2ed4543ad46f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add foreign key from chat sessions to leads."""

    op.create_foreign_key(
        "fk_chat_sessions_lead_id",
        "chat_sessions",
        "leads",
        ["lead_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove foreign key from chat sessions."""

    op.drop_constraint(
        "fk_chat_sessions_lead_id",
        "chat_sessions",
        type_="foreignkey",
    )
