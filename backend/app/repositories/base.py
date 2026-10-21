"""Generisches BaseRepository mit CRUD-Operationen (async SQLAlchemy)."""
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import delete as sa_delete, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generisches async Repository mit Standard-CRUD.

    Nutzung:
        class UserRepo(BaseRepository[User]):
            def __init__(self, session):
                super().__init__(session, User)
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelT]):
        self.session = session
        self.model_class = model_class

    # ── Create ────────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelT:
        """Erzeugt eine neue Instanz und gibt sie zurück."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    # ── Read ──────────────────────────────────────────────────────────────

    async def get(self, id: Any) -> Optional[ModelT]:
        """Liest ein Objekt anhand seiner ID (Primary Key)."""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *filters: Any,
        order_by: Optional[Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[ModelT]:
        """Listet alle Objekte, optional gefiltert."""
        stmt = select(self.model_class)
        for f in filters:
            stmt = stmt.where(f)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelT]:
        """Liest ein Objekt anhand eines Feldnamens (z. B. email)."""
        column = getattr(self.model_class, field, None)
        if column is None:
            raise ValueError(f"Field '{field}' does not exist on {self.model_class.__name__}")
        stmt = select(self.model_class).where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Update ────────────────────────────────────────────────────────────

    async def update(self, id: Any, **kwargs: Any) -> Optional[ModelT]:
        """Aktualisiert Felder und gibt das aktualisierte Objekt zurück."""
        stmt = (
            sa_update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def update_orm(self, id: Any, **kwargs: Any) -> Optional[ModelT]:
        """ORM-basiertes Update: Holt, setzt, flushed. Arbeitet auch mit
        Beziehungen / event-getriggerten Änderungen besser."""
        obj = await self.get(id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete(self, id: Any) -> bool:
        """Löscht ein Objekt. Gibt True zurück wenn gelöscht."""
        stmt = sa_delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    # ── Count ─────────────────────────────────────────────────────────────

    async def count(self, *filters: Any) -> int:
        """Zählt Objekte (optional gefiltert)."""
        from sqlalchemy import func, select as sel

        stmt = sel(func.count()).select_from(self.model_class)
        for f in filters:
            stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar_one()