"""IngredientRepository – DB-Zugriff auf Ingredients."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Ingredient
from app.repositories.base import BaseRepository


class IngredientRepository(BaseRepository[Ingredient]):
    """Repository für Ingredient-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Ingredient)

    async def get_by_category(self, category: str) -> list[Ingredient]:
        """Listet alle Zutaten einer Kategorie."""
        return await self.get_all(self.model_class.category == category)

    async def get_by_name(self, name: str) -> Optional[Ingredient]:
        """Findet eine Zutat exakt per Name."""
        return await self.get_by_field("name", name)

    async def search_by_name(self, query: str) -> list[Ingredient]:
        """Volltext-ähnliche Suche über Zutatennamen (case-insensitive)."""
        from sqlalchemy import func

        stmt = (
            select(self.model_class)
            .where(self.model_class.name.ilike(f"%{query}%"))
            .order_by(self.model_class.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())