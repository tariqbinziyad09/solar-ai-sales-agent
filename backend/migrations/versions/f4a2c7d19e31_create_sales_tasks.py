"""create sales tasks

Revision ID: f4a2c7d19e31
Revises: 8d6f4b21c9a7
"""

import sqlalchemy as sa
from alembic import op

revision = "f4a2c7d19e31"
down_revision = "8d6f4b21c9a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "priority", sa.String(length=20), nullable=False, server_default="medium"
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.getdate(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.getdate(),
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_tasks_lead_id", "sales_tasks", ["lead_id"])


def downgrade():
    op.drop_index("ix_sales_tasks_lead_id", table_name="sales_tasks")
    op.drop_table("sales_tasks")
