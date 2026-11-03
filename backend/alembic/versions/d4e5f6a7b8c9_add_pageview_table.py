"""add_pageview_table

Revision ID: d4e5f6a7b8c9
Revises: b7f8c9d0e1f2
Create Date: 2026-11-01 13:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b7f8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pageview',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('path', sa.String(500), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),
        sa.Column('session_hash', sa.String(64), nullable=True),
        sa.Column('device', sa.String(20), nullable=True),
    )
    op.create_index('ix_pageview_created_at', 'pageview', ['created_at'])
    op.create_index('ix_pageview_utm_source', 'pageview', ['utm_source'])
    op.create_index('ix_pageview_session_hash', 'pageview', ['session_hash'])


def downgrade() -> None:
    op.drop_index('ix_pageview_session_hash', table_name='pageview')
    op.drop_index('ix_pageview_utm_source', table_name='pageview')
    op.drop_index('ix_pageview_created_at', table_name='pageview')
    op.drop_table('pageview')
