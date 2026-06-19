"""add_entities_and_document_entities_tables

Revision ID: 1ac1dd712db6
Revises: 2a505228d2d8
Create Date: 2026-06-15 07:48:39.874966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1ac1dd712db6'
down_revision: Union[str, Sequence[str], None] = '2a505228d2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "name", "type", name="uq_entity_workspace_name_type"),
    )
    op.create_index(op.f("ix_entities_workspace_id"), "entities", ["workspace_id"])

    op.create_table(
        "document_entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_id", "entity_id", name="uq_document_entity"),
    )
    op.create_index(op.f("ix_document_entities_file_id"), "document_entities", ["file_id"])
    op.create_index(op.f("ix_document_entities_entity_id"), "document_entities", ["entity_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_document_entities_entity_id"), table_name="document_entities")
    op.drop_index(op.f("ix_document_entities_file_id"), table_name="document_entities")
    op.drop_table("document_entities")

    op.drop_index(op.f("ix_entities_workspace_id"), table_name="entities")
    op.drop_table("entities")
