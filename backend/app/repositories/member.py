"""MemberRepository – DB-Zugriff auf Members."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Member
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    """Repository für Member-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Member)

    async def get_by_household(self, household_id: object) -> list[Member]:
        """Alle Members eines Households."""
        return await self.get_all(self.model_class.household_id == household_id)

    async def get_active_by_household(self, household_id: object) -> list[Member]:
        """Nur aktive Members eines Households."""
        return await self.get_all(
            self.model_class.household_id == household_id,
            self.model_class.is_active.is_(True),
        )

    async def clear_allergies(self, household_id: object) -> int:
        """Löscht die Allergien aller Mitglieder eines Haushalts.

        Wird beim Widerruf der Einwilligung nach Art. 9 DSGVO aufgerufen.
        Allergien sind Gesundheitsdaten; nach dem Widerruf dürfen sie nicht
        weiter gespeichert werden (Art. 7 Abs. 3 DSGVO). Ein bloßer
        Zeitstempel im Profil genügt dafür nicht.
        """
        members = await self.get_by_household(household_id)
        betroffen = 0
        for member in members:
            if member.allergies:
                member.allergies = []
                betroffen += 1
        await self.session.flush()
        return betroffen