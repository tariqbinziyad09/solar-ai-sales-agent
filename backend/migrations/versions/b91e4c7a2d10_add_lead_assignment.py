"""add lead assignment

Revision ID: b91e4c7a2d10
Revises: a7d9e21b4c10
Create Date: 2026-09-29

Adds staff ownership/assignment support to CRM leads.

A lead may remain unassigned (NULL), which is important because
customer-facing AI can create leads before a sales executive is
selected by an Admin or Sales Manager.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# ------------------------------------------------------------------
# ALEMBIC REVISION IDENTIFIERS
# ------------------------------------------------------------------

revision: str = "b91e4c7a2d10"
down_revision: str | None = "a7d9e21b4c10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add assigned_to_user_id to leads.

    NULL:
        Lead is currently unassigned.

    Integer user ID:
        Lead belongs to that internal staff member.

    If a staff user is deleted, SET NULL keeps the customer lead
    instead of deleting CRM data.
    """

    op.add_column(
        "leads",
        sa.Column(
            "assigned_to_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_leads_assigned_to_user_id",
        "leads",
        ["assigned_to_user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_leads_assigned_to_user_id_users",
        "leads",
        "users",
        ["assigned_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """
    Safely remove lead assignment support.
    """

    op.drop_constraint(
        "fk_leads_assigned_to_user_id_users",
        "leads",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_leads_assigned_to_user_id",
        table_name="leads",
    )

    op.drop_column(
        "leads",
        "assigned_to_user_id",
    )
