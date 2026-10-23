"""add_reset_token_to_users

Revision ID: 0c3b8a4f6e2d
Revises: 539a1c47c6d2
Create Date: 2026-10-23 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0c3b8a4f6e2d'
down_revision: Union[str, None] = '539a1c47c6d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('reset_token', sa.String(128), nullable=True)
    )
    op.add_column('users',
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(op.f('ix_users_reset_token'), 'users', ['reset_token'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_reset_token'), table_name='users')
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')