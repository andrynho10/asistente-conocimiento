"""Add cache_hit column to queries table - Task 6 (AC#2)

Revision ID: add_cache_hit_to_queries
Revises: create_queries_table
Create Date: 2025-11-14

This migration adds the cache_hit boolean column to the queries table
to track whether responses were served from cache (Story 3.6, Task 6).
Note: The queries table is created in a separate migration (create_queries_table).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_cache_hit_to_queries'
down_revision: Union[str, Sequence[str], None] = 'create_queries_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - cache_hit column already exists in queries table.

    This migration is a no-op because cache_hit is already included in
    the create_queries_table migration. Kept for migration history.
    """
    # No-op: cache_hit is already created in create_queries_table
    pass


def downgrade() -> None:
    """Downgrade schema - no-op downgrade (see upgrade note)."""
    # No-op: this migration doesn't modify the schema
    pass
