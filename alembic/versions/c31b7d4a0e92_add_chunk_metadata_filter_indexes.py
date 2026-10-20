"""add chunk metadata filter indexes

Revision ID: c31b7d4a0e92
Revises: b41d2a8c7e90
Create Date: 2026-10-20
"""

from alembic import op


revision = "c31b7d4a0e92"
down_revision = "b41d2a8c7e90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The retriever compares these JSONB scalar fields with equality.
    op.execute("CREATE INDEX ix_chunks_metadata_device ON chunks ((metadata ->> 'device'))")
    op.execute("CREATE INDEX ix_chunks_metadata_brand ON chunks ((metadata ->> 'brand'))")


def downgrade() -> None:
    op.execute("DROP INDEX ix_chunks_metadata_brand")
    op.execute("DROP INDEX ix_chunks_metadata_device")
