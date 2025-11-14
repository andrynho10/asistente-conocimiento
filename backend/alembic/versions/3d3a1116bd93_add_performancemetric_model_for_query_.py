"""Add PerformanceMetric model for query tracking - clean

Revision ID: 3d3a1116bd93
Revises: ad947522f5ce
Create Date: 2025-11-13 21:06:47.912359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d3a1116bd93'
down_revision: Union[str, Sequence[str], None] = 'f24f93ff1ff8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create performance_metrics table
    op.create_table(
        'performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('retrieval_time_ms', sa.Float(), nullable=False),
        sa.Column('llm_time_ms', sa.Float(), nullable=False),
        sa.Column('total_time_ms', sa.Float(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['query_id'], ['queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes
    op.create_index('ix_performance_metrics_query_id', 'performance_metrics', ['query_id'])
    op.create_index('ix_performance_metrics_created_at', 'performance_metrics', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop performance_metrics table
    op.drop_index('ix_performance_metrics_created_at', 'performance_metrics')
    op.drop_index('ix_performance_metrics_query_id', 'performance_metrics')
    op.drop_table('performance_metrics')
