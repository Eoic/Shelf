"""Switch to Crockford Base32 string IDs for all models

Revision ID: 983f05a87193
Revises: 
Create Date: 2025-06-16 22:22:13.279601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '983f05a87193'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('books',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('authors', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('publication_date', sa.String(), nullable=True),
    sa.Column('isbn_10', sa.String(), nullable=True),
    sa.Column('isbn_13', sa.String(), nullable=True),
    sa.Column('language', sa.String(), nullable=True),
    sa.Column('series_name', sa.String(), nullable=True),
    sa.Column('series_index', sa.Float(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('identifiers', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), nullable=True),
    sa.Column('covers', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), nullable=False),
    sa.Column('format', sa.String(), nullable=True),
    sa.Column('original_filename', sa.String(), nullable=True),
    sa.Column('stored_filename', sa.String(), nullable=True),
    sa.Column('file_hash', sa.String(), nullable=True),
    sa.Column('file_path', sa.String(), nullable=True),
    sa.Column('file_size_bytes', sa.Integer(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('file_hash')
    )
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('storage',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('config', sa.JSON(), nullable=False),
    sa.Column('storage_type', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('is_default', sa.Boolean(), nullable=False, comment='Indicates whether this is the primary (default) storage for the user. Only one storage entry per user can have this set to True.'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_storage_id'), 'storage', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_storage_id'), table_name='storage')
    op.drop_table('storage')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_books_id'), table_name='books')
    op.drop_table('books')
    # ### end Alembic commands ###
