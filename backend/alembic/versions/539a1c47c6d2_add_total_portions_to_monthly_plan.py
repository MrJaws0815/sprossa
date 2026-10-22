"""add_total_portions_to_monthly_plan

Revision ID: 539a1c47c6d2
Revises: c2adb48c467b
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '539a1c47c6d2'
down_revision: Union[str, None] = 'c2adb48c467b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('monthly_plans',
        sa.Column('total_portions', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('monthly_plans', 'total_portions')