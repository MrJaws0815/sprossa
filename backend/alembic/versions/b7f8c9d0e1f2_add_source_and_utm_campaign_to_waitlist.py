"""add_source_and_utm_campaign_to_waitlist

Revision ID: b7f8c9d0e1f2
Revises: 0c3b8a4f6e2d
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7f8c9d0e1f2'
down_revision: Union[str, None] = '0c3b8a4f6e2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('waitlist',
        sa.Column('source', sa.String(100), nullable=True)
    )
    op.add_column('waitlist',
        sa.Column('utm_campaign', sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('waitlist', 'source')
    op.drop_column('waitlist', 'utm_campaign')
