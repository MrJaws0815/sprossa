"""Löscht Pageview-Datensätze nach Ablauf der Aufbewahrungsfrist.

Die Datenschutzerklärung sagt 90 Tage zu (Abschnitt „Reichweitenmessung").
Ohne diesen Job wächst die Tabelle unbegrenzt weiter und die Zusage wäre
falsch — genau der Punkt, den der Rechtsseiten-Audit als Lücke 4 benannt hat.

Aufruf (täglich per Cron auf dem Server):

    docker exec sprossa-backend-1 python -m app.jobs.purge_pageviews

Die Frist lässt sich über MM_PAGEVIEW_RETENTION_DAYS ändern; Default 90.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete

from app.core.config import settings
from app.core.database import async_session_factory, engine
from app.models.database import PageviewModel

logger = logging.getLogger(__name__)


async def purge(days: int | None = None) -> int:
    """Löscht alle Pageviews, die älter als `days` Tage sind. Gibt die Anzahl zurück."""
    retention = days if days is not None else settings.pageview_retention_days
    cutoff = datetime.now(UTC) - timedelta(days=retention)

    async with async_session_factory() as session:
        result = await session.execute(
            delete(PageviewModel).where(PageviewModel.created_at < cutoff)
        )
        await session.commit()
        deleted = result.rowcount or 0

    logger.info("Pageview-Aufräumung: %s Zeilen älter als %s Tage gelöscht", deleted, retention)
    return deleted


async def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Die Engine loggt bei MM_DEBUG=true jedes SQL. Für einen Cron-Job ist das
    # nur Rauschen im Log.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    deleted = await purge()
    print(f"purge_pageviews: {deleted} Zeilen gelöscht (Frist {settings.pageview_retention_days} Tage)")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
