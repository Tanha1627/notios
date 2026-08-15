"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "workspaces",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", sa.CHAR(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "pages",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("workspace_id", sa.CHAR(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("parent_page_id", sa.CHAR(36), sa.ForeignKey("pages.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("created_by", sa.CHAR(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "blocks",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("page_id", sa.CHAR(36), sa.ForeignKey("pages.id"), nullable=False),
        sa.Column("parent_block_id", sa.CHAR(36), sa.ForeignKey("blocks.id"), nullable=True),
        sa.Column(
            "type",
            sa.Enum("text", "heading", "todo", "bullet", "image", name="blocktype"),
            nullable=False,
        ),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("page_id", sa.CHAR(36), sa.ForeignKey("pages.id"), nullable=False),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "role", sa.Enum("owner", "editor", "viewer", name="roleenum"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime),
        sa.UniqueConstraint("page_id", "user_id", name="uq_page_user"),
    )


def downgrade() -> None:
    op.drop_table("permissions")
    op.drop_table("blocks")
    op.drop_table("pages")
    op.drop_table("workspaces")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS blocktype")
    op.execute("DROP TYPE IF EXISTS roleenum")
