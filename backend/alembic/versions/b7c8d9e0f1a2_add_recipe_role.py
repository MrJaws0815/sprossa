"""add recipe_role to recipes

Beilagen (Rotkohl, Dips, Salate) sind keine vollstaendigen Mahlzeiten und
duerfen nicht als Abendessen im Monatsplan landen. Statt sie zu loeschen
bleiben sie erhalten (fuer spaetere Kombi-Funktionen) und werden nur
anders eingeordnet.

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-11-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'recipes',
        sa.Column('recipe_role', sa.String(20), nullable=False, server_default='main'),
    )
    op.create_index('ix_recipes_recipe_role', 'recipes', ['recipe_role'])


def downgrade() -> None:
    op.drop_index('ix_recipes_recipe_role', table_name='recipes')
    op.drop_column('recipes', 'recipe_role')
