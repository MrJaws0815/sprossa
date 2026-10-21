"""PlanRepository – DB-Zugriff auf WeeklyPlans, MonthlyPlans, MealSlots."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import MealSlot, MonthlyPlan, WeeklyPlan
from app.repositories.base import BaseRepository


class WeeklyPlanRepository(BaseRepository[WeeklyPlan]):
    """Repository für WeeklyPlan-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WeeklyPlan)

    async def get_with_slots(self, plan_id: object) -> Optional[WeeklyPlan]:
        """Lädt einen Wochenplan inklusive aller MealSlots."""
        stmt = (
            select(WeeklyPlan)
            .where(WeeklyPlan.id == plan_id)
            .options(selectinload(WeeklyPlan.meal_slots))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_household(self, household_id: object) -> list[WeeklyPlan]:
        """Alle Wochenpläne eines Households."""
        return await self.get_all(self.model_class.household_id == household_id)


class MonthlyPlanRepository(BaseRepository[MonthlyPlan]):
    """Repository für MonthlyPlan-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MonthlyPlan)

    async def get_with_weekly(self, plan_id: object) -> Optional[MonthlyPlan]:
        """Monatsplan inklusive Wochenplänen."""
        stmt = (
            select(MonthlyPlan)
            .where(MonthlyPlan.id == plan_id)
            .options(selectinload(MonthlyPlan.weekly_plans))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_for_household(
        self, household_id: object
    ) -> Optional[MonthlyPlan]:
        """Neuesten Monatsplan eines Households (nach Jahr/Monat absteigend)."""
        stmt = (
            select(MonthlyPlan)
            .where(MonthlyPlan.household_id == household_id)
            .order_by(MonthlyPlan.year.desc(), MonthlyPlan.month.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MealSlotRepository(BaseRepository[MealSlot]):
    """Repository für MealSlot-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MealSlot)

    async def get_by_week(self, weekly_plan_id: object) -> list[MealSlot]:
        """Alle Slots eines Wochenplans."""
        return await self.get_all(
            self.model_class.weekly_plan_id == weekly_plan_id,
            order_by=MealSlot.day_of_week,
        )