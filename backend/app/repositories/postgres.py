"""PostgreSQL-Repository-Implementierungen (async)."""
from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4
import secrets

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import WaitlistEntryModel
from app.repositories import WaitlistEntry


def generate_token(length: int = 48) -> str:
    """Erzeugt einen kryptografisch sicheren Token (URL-sicher)."""
    return secrets.token_urlsafe(length)


class PostgresWaitlistRepo:
    """PostgreSQL-Implementierung der Waitlist (async)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entry: WaitlistEntry) -> WaitlistEntry:
        model = WaitlistEntryModel(
            email=entry.email,
            name=entry.name,
            household_size=entry.household_size,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return WaitlistEntry(
            id=str(model.id),
            email=model.email,
            name=model.name,
            household_size=model.household_size,
            created_at=model.created_at,
            confirmed_at=model.confirmed_at,
            confirmation_token=model.confirmation_token,
        )

    async def get_by_email(self, email: str) -> Optional[WaitlistEntry]:
        stmt = select(WaitlistEntryModel).where(WaitlistEntryModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entry(model)

    async def get_by_token(self, token: str) -> Optional[WaitlistEntry]:
        stmt = select(WaitlistEntryModel).where(
            WaitlistEntryModel.confirmation_token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entry(model) if model else None

    async def set_confirmation_token(self, entry_id: str, token: str) -> None:
        from uuid import UUID
        from sqlalchemy import update
        q = (
            update(WaitlistEntryModel)
            .where(WaitlistEntryModel.id == UUID(entry_id))
            .values(confirmation_token=token, confirmation_sent_at=datetime.now(UTC))
        )
        await self.session.execute(q)
        await self.session.flush()

    async def confirm_by_token(self, token: str, ip: str = "") -> Optional[WaitlistEntry]:
        from sqlalchemy import update
        from uuid import UUID

        # Erst das Modell finden
        stmt = select(WaitlistEntryModel).where(
            WaitlistEntryModel.confirmation_token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None or model.confirmed_at is not None:
            return None  # bereits bestätigt oder Token ungültig

        # Token löschen + confirmed setzen
        q = (
            update(WaitlistEntryModel)
            .where(WaitlistEntryModel.id == model.id)
            .values(
                confirmed_at=datetime.now(UTC),
                confirmed_ip=ip if ip else None,
                confirmation_token=None,
            )
        )
        await self.session.execute(q)
        await self.session.flush()

        # Aktualisierten Eintrag zurückgeben
        model.confirmed_at = datetime.now(UTC)
        model.confirmation_token = None
        return self._model_to_entry(model)

    async def count(self) -> int:
        stmt = select(func.count(WaitlistEntryModel.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_confirmed(self) -> int:
        stmt = select(func.count(WaitlistEntryModel.id)).where(
            WaitlistEntryModel.confirmed_at.isnot(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ─── Helfer ────────────────────────────────────────────────

    @staticmethod
    def _model_to_entry(model: WaitlistEntryModel) -> WaitlistEntry:
        return WaitlistEntry(
            id=str(model.id),
            email=model.email,
            name=model.name,
            household_size=model.household_size,
            created_at=model.created_at,
            confirmed_at=model.confirmed_at,
            confirmation_token=model.confirmation_token,
            confirmation_sent_at=model.confirmation_sent_at,
        )