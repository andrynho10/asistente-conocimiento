"""Add security fields to User table: last_login, failed_login_attempts, locked_until

Revision ID: add_user_security_fields
Revises: cebc7701286d
Create Date: 2025-11-14 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_security_fields'
down_revision: Union[str, Sequence[str], None] = 'cebc7701286d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add security fields to User table."""
    # Add last_login column
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))

    # Add failed_login_attempts column with default value of 0
    op.add_column('user', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))

    # Add locked_until column for account locking
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove security fields from User table."""
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'failed_login_attempts')
    op.drop_column('user', 'last_login')
