"""Add generated_content table for Story 4.1

Revision ID: add_generated_content_table
Revises: add_cache_hit_to_queries
Create Date: 2025-11-14

This migration creates the generated_content table to store AI-generated
content (summaries, quizzes, learning paths) with caching support (Story 4.1, Task 1).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_generated_content_table'
down_revision: Union[str, Sequence[str], None] = 'add_cache_hit_to_queries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create generated_content table."""
    # Create generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes for efficient caching queries
    op.create_index(
        'ix_generated_content_document_id',
        'generated_content',
        ['document_id']
    )
    op.create_index(
        'ix_generated_content_user_id',
        'generated_content',
        ['user_id']
    )
    op.create_index(
        'ix_generated_content_content_type',
        'generated_content',
        ['content_type']
    )
    op.create_index(
        'ix_generated_content_doc_type_created',
        'generated_content',
        ['document_id', 'content_type', 'created_at']
    )
    op.create_index(
        'ix_generated_content_created_at',
        'generated_content',
        ['created_at']
    )


def downgrade() -> None:
    """Downgrade schema - drop generated_content table."""
    op.drop_index('ix_generated_content_created_at', 'generated_content')
    op.drop_index('ix_generated_content_doc_type_created', 'generated_content')
    op.drop_index('ix_generated_content_content_type', 'generated_content')
    op.drop_index('ix_generated_content_user_id', 'generated_content')
    op.drop_index('ix_generated_content_document_id', 'generated_content')
    op.drop_table('generated_content')
