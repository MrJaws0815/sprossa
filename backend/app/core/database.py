"""Async-Datenbank-Engine & Session"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# In Tests: NullPool, damit jede Testfunktion (eigener Event-Loop) eine frische
# Connection bekommt. Sonst: "Future attached to a different loop" / MissingGreenlet.
_engine_kwargs = {"echo": settings.debug}
if os.getenv("MM_TESTING", "").lower() in ("1", "true", "yes"):
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(settings.database_url, **_engine_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI-Dependency: gibt eine asynchrone DB-Session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise