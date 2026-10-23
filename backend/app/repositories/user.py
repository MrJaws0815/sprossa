"""UserRepository – DB-Zugriff auf Users."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository für User-Tabelle."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Findet einen User per E-Mail."""
        return await self.get_by_field("email", email)

    async def create_user(
        self, email: str, password_hash: str, display_name: str
    ) -> User:
        """Erzeugt einen neuen User."""
        return await self.create(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )

    async def get_by_stripe_customer(self, stripe_customer_id: str) -> Optional[User]:
        """Findet User via Stripe-Customer-ID."""
        return await self.get_by_field("stripe_customer_id", stripe_customer_id)

    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """Findet User via reset_token."""
        return await self.get_by_field("reset_token", token)