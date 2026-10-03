"""create lead notes

Revision ID: c31f6a8d2e40
Revises: b91e4c7a2d10
"""
from alembic import op
import sqlalchemy as sa

revision = "c31f6a8d2e40"
down_revision = "b91e4c7a2d10"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "lead_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lead_notes_lead_id", "lead_notes", ["lead_id"], unique=False)
    op.create_index(
        "ix_lead_notes_author_user_id",
        "lead_notes",
        ["author_user_id"],
        unique=False,
    )

def downgrade():
    op.drop_index("ix_lead_notes_author_user_id", table_name="lead_notes")
    op.drop_index("ix_lead_notes_lead_id", table_name="lead_notes")
    op.drop_table("lead_notes")
