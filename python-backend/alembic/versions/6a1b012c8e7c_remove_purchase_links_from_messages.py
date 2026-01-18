"""remove_purchase_links_from_messages

Revision ID: 6a1b012c8e7c
Revises: a8abefa4ec5f
Create Date: 2026-01-18 14:08:09.309784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a1b012c8e7c'
down_revision: Union[str, Sequence[str], None] = 'a8abefa4ec5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove purchase_links column from conversation_messages table
    op.drop_column('conversation_messages', 'purchase_links')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back purchase_links column to conversation_messages table
    op.add_column('conversation_messages', sa.Column('purchase_links', sa.JSON(), nullable=True))
