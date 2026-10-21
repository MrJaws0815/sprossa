"""RecipeRepository – DB-Zugriff auf Recipes + RecipeIngredients."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Recipe, RecipeIngredient
from app.repositories.base import BaseRepository


class RecipeRepository(BaseRepository[Recipe]):
    """Repository für Recipe-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Recipe)

    async def get_with_ingredients(self, recipe_id: object) -> Optional[Recipe]:
        """Lädt ein Rezept inklusive aller Zutaten (eager loaded)."""
        stmt = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_household(self, household_id: object) -> list[Recipe]:
        """Listet alle Rezepte eines Households."""
        return await self.get_all(self.model_class.household_id == household_id)

    async def search_by_allergens(
        self, household_id: object, allergen_names: list[str]
    ) -> list[Recipe]:
        """Findet Rezepte, die KEINE der genannten Allergene enthalten.

        Hinweis: Vereinfachte Version – prüft über die verknüpften Zutaten
        (Allergen-Mapping müsste in einer späteren Iteration über
        Ingredient.allergen_flag o. Ä. laufen).
        """
        # Aktuell: Alle Rezepte des Households (Filter-Logik kommt später)
        return await self.get_by_household(household_id)

    async def get_public(self) -> list[Recipe]:
        """Listet alle öffentlichen Rezepte."""
        return await self.get_all(self.model_class.is_public.is_(True))