"""add health_data_consent_at to households

Art. 9 DSGVO: Allergien sind Gesundheitsdaten. Der Zeitstempel dokumentiert die
ausdrueckliche Einwilligung; NULL = keine Einwilligung erteilt. Der Zeitstempel
wird bei Widerruf bewusst NICHT geloescht, damit der Nachweis erhalten bleibt.

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-11-05 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'households',
        sa.Column('health_data_consent_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('households', 'health_data_consent_at')
