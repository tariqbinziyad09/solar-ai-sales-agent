"""create internal users

Revision ID: a7d9e21b4c10
Revises: f4a2c7d19e31

The original local SQL Server database already contained this table and the
historical migration was intentionally empty. A fresh cloud database needs the
schema, so this migration now creates it portably for PostgreSQL as well.
"""

import sqlalchemy as sa
from alembic import op

revision = "a7d9e21b4c10"
down_revision = "f4a2c7d19e31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="sales_executive",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade():
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
