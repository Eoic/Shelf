"""Add status and processing_error fields to Book

Revision ID: 20250617_add_book_status
Revises: 983f05a87193
Create Date: 2025-06-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250617_add_book_status"
down_revision = "983f05a87193"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "books",
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
    )
    op.add_column("books", sa.Column("processing_error", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("books", "processing_error")
    op.drop_column("books", "status")
