"""add chunks vector store

Revision ID: b41d2a8c7e90
Revises: affaba139657
Create Date: 2026-10-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b41d2a8c7e90"
down_revision: Union[str, Sequence[str], None] = "affaba139657"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("chunk_key", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_key"),
    )
    # Alembic has no portable Vector type. Convert the temporary text column to
    # pgvector's real type before creating the approximate nearest-neighbour index.
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(384) USING embedding::vector")
    op.execute(
        "CREATE INDEX ix_chunks_embedding_ivfflat "
        "ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("chunks")
