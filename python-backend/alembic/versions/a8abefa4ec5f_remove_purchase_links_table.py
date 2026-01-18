"""remove_purchase_links_table

Revision ID: a8abefa4ec5f
Revises: 70e2f3202201
Create Date: 2026-01-18 14:07:50.946958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8abefa4ec5f'
down_revision: Union[str, Sequence[str], None] = '70e2f3202201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove purchase_links table
    op.drop_table('purchase_links')


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate purchase_links table
    op.create_table(
        'purchase_links',
        sa.Column('link_id', sa.String(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=True),
        sa.Column('link_type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('display_text', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=True),
        sa.Column('price', sa.String(), nullable=True),
        sa.Column('availability', sa.String(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('link_id')
    )
