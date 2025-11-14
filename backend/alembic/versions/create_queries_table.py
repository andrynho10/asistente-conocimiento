"""Create queries table for RAG query audit logging

Revision ID: create_queries_table
Revises: 3d3a1116bd93
Create Date: 2025-11-14

This migration creates the queries table for storing RAG queries
and related metadata for audit logging and performance tracking
(Story 3.4, AC#8 and Story 3.6, Task 6: AC#2).

Includes:
- cache_hit field to track caching performance (Task 6: AC#2)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'create_queries_table'
down_revision: Union[str, Sequence[str], None] = '3d3a1116bd93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create queries table."""
    # Create queries table with cache_hit field (Task 6: AC#2)
    op.create_table(
        'queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(), nullable=False),
        sa.Column('answer_text', sa.String(), nullable=False),
        sa.Column('sources_json', sa.String(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('sources_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes
    op.create_index('ix_queries_query_text', 'queries', ['query_text'])
    op.create_index('ix_queries_user_id', 'queries', ['user_id'])
    op.create_index('ix_queries_created_at', 'queries', ['created_at'])


def downgrade() -> None:
    """Downgrade schema - drop queries table."""
    # Drop indexes
    op.drop_index('ix_queries_created_at', 'queries')
    op.drop_index('ix_queries_user_id', 'queries')
    op.drop_index('ix_queries_query_text', 'queries')
    # Drop table
    op.drop_table('queries')
