"""HouseholdRepository – DB-Zugriff auf Households + Member-Verwaltung."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Household, Member
from app.repositories.base import BaseRepository


class HouseholdRepository(BaseRepository[Household]):
    """Repository für Household-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Household)

    async def create_with_members(
        self, name: str, user_id: object, members: list[dict] | None = None
    ) -> Household:
        """Erzeugt einen Household + optionale Members in einer Transaktion."""
        household = await self.create(name=name, user_id=user_id)
        if members:
            from app.models.database import Member

            for m in members:
                member = Member(household_id=household.id, **m)
                self.session.add(member)
            await self.session.flush()
        await self.session.refresh(household)
        return household

    async def get_by_owner(self, user_id: object) -> list[Household]:
        """Listet alle Households eines Owners."""
        return await self.get_all(self.model_class.user_id == user_id)