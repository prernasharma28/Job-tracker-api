"""Initial database schema

Revision ID: a18fe1b6d822
Revises:
Create Date: 2026-09-09 12:22:02.762385

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a18fe1b6d822"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "applications",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_applications_id",
        "applications",
        ["id"],
        unique=False,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.create_index(
        "ix_refresh_tokens_id",
        "refresh_tokens",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop initial database schema."""

    op.drop_table("refresh_tokens")
    op.drop_table("applications")
    op.drop_table("users")