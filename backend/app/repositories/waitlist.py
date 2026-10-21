"""WaitlistRepository – DB-Zugriff auf die Beta-Warteschlange.

Baut auf dem bestehenden PostgresWaitlistRepo auf und erweitert es um
das generische BaseRepository-Interface.
"""
from datetime import UTC, datetime
from typing import Optional
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import WaitlistEntryModel
from app.repositories.base import BaseRepository


def generate_token(length: int = 48) -> str:
    """Kryptografisch sicherer URL-Token."""
    return secrets.token_urlsafe(length)


class WaitlistRepository(BaseRepository[WaitlistEntryModel]):
    """Repository für die Waitlist-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WaitlistEntryModel)

    async def get_by_email(self, email: str) -> Optional[WaitlistEntryModel]:
        """Findet einen Wartelisten-Eintrag per E-Mail."""
        return await self.get_by_field("email", email)

    async def get_by_token(self, token: str) -> Optional[WaitlistEntryModel]:
        """Findet einen Eintrag per Confirmation-Token."""
        return await self.get_by_field("confirmation_token", token)

    async def create_entry(
        self, email: str, name: str | None = None, household_size: int | None = None
    ) -> WaitlistEntryModel:
        """Legt einen neuen Wartelisten-Eintrag an."""
        return await self.create(
            email=email,
            name=name,
            household_size=household_size,
        )

    async def confirm(self, email: str) -> Optional[WaitlistEntryModel]:
        """Bestätigt einen Eintrag (setzt confirmed_at)."""
        entry = await self.get_by_email(email)
        if entry is None:
            return None
        entry.confirmed_at = datetime.now(UTC)
        entry.confirmation_token = None
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def set_confirmation_token(
        self, entry_id: object, token: str
    ) -> None:
        """Setzt den Confirmation-Token + Sendezeitstempel."""
        await self.update(
            entry_id,
            confirmation_token=token,
            confirmation_sent_at=datetime.now(UTC),
        )

    async def confirm_by_token(
        self, token: str, ip: str = ""
    ) -> Optional[WaitlistEntryModel]:
        """Bestätigt via Token und gibt den aktualisierten Eintrag zurück."""
        entry = await self.get_by_token(token)
        if entry is None or entry.confirmed_at is not None:
            return None
        entry.confirmed_at = datetime.now(UTC)
        entry.confirmed_ip = ip or None
        entry.confirmation_token = None
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def count_confirmed(self) -> int:
        """Anzahl bestätigter Einträge."""
        from sqlalchemy import func

        stmt = select(func.count()).where(
            self.model_class.confirmed_at.isnot(None)
        ).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar_one()