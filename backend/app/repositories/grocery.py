"""GroceryRepository – DB-Zugriff auf GroceryLists + GroceryItems."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import GroceryItem, GroceryList
from app.repositories.base import BaseRepository


class GroceryListRepository(BaseRepository[GroceryList]):
    """Repository für GroceryList-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, GroceryList)

    async def get_with_items(self, list_id: object) -> Optional[GroceryList]:
        """Lädt eine Einkaufsliste inklusive Items."""
        stmt = (
            select(GroceryList)
            .where(GroceryList.id == list_id)
            .options(selectinload(GroceryList.items))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_plan(
        self, monthly_plan_id: object, week_number: Optional[int] = None
    ) -> list[GroceryList]:
        """Findet Einkaufslisten zu einem Plan (optional gefiltert auf Woche)."""
        filters = [self.model_class.monthly_plan_id == monthly_plan_id]
        if week_number is not None:
            filters.append(self.model_class.week_number == week_number)
        return await self.get_all(*filters)

    async def get_by_household(self, household_id: object) -> list[GroceryList]:
        """Alle Einkaufslisten eines Households."""
        return await self.get_all(self.model_class.household_id == household_id)

    async def create_from_plan(
        self, household_id: object, monthly_plan_id: object, week_number: int | None = None
    ) -> GroceryList:
        """Erzeugt eine neue Einkaufsliste aus einem Plan."""
        return await self.create(
            household_id=household_id,
            monthly_plan_id=monthly_plan_id,
            week_number=week_number,
            is_master_list=(week_number is None),
        )


class GroceryItemRepository(BaseRepository[GroceryItem]):
    """Repository für GroceryItem-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, GroceryItem)

    async def get_by_list(self, grocery_list_id: object) -> list[GroceryItem]:
        """Alle Items einer Einkaufsliste."""
        return await self.get_all(self.model_class.grocery_list_id == grocery_list_id)