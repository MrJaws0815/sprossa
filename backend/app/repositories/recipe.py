"""RecipeRepository – DB-Zugriff auf Recipes + RecipeIngredients."""
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    MealSlot, MonthlyPlan, Recipe, RecipeIngredient, WeeklyPlan,
)
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
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_household(self, household_id: object) -> list[Recipe]:
        """Listet alle Rezepte eines Households."""
        return await self.get_all(self.model_class.household_id == household_id)

    async def list_filtered(
        self,
        household_ids: list,
        planned_only: bool = False,
        search: Optional[str] = None,
        difficulty: Optional[str] = None,
        max_time: Optional[int] = None,
        tag: Optional[str] = None,
    ) -> list[Recipe]:
        """Rezeptliste mit optionalen Filtern (GET /recipes).

        planned_only=True liefert nur Rezepte, die in MealSlots der Pläne
        der angegebenen Haushalte vorkommen (DISTINCT recipe_id).
        """
        stmt = select(Recipe)
        if planned_only:
            if not household_ids:
                return []
            planned_ids = (
                select(MealSlot.recipe_id)
                .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
                .join(MonthlyPlan, WeeklyPlan.monthly_plan_id == MonthlyPlan.id)
                .where(MonthlyPlan.household_id.in_(household_ids))
                .distinct()
            )
            stmt = stmt.where(Recipe.id.in_(planned_ids))
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(or_(
                Recipe.title.ilike(pattern),
                Recipe.description.ilike(pattern),
            ))
        if difficulty:
            stmt = stmt.where(Recipe.difficulty == difficulty)
        if max_time is not None:
            total_time = func.coalesce(Recipe.prep_time_minutes, 0) + func.coalesce(
                Recipe.cook_time_minutes, 0
            )
            stmt = stmt.where(total_time <= max_time)
        if tag:
            stmt = stmt.where(Recipe.tags.contains([tag]))
        stmt = stmt.order_by(Recipe.title)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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