"""Test für den Pageview-Löschjob (Lücke 4 aus dem Rechtsseiten-Audit).

Die Datenschutzerklärung sagt 90 Tage Aufbewahrung zu. Der Job muss genau
das durchsetzen: alles Ältere weg, alles Jüngere bleibt.
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.database import async_session_factory
from app.jobs.purge_pageviews import purge
from app.models.database import PageviewModel


@pytest.mark.asyncio
async def test_purge_loescht_nur_alte_pageviews():
    tag = uuid.uuid4().hex[:8]
    alt = f"/alt-{tag}"
    frisch = f"/neu-{tag}"

    async with async_session_factory() as session:
        session.add_all([
            PageviewModel(
                created_at=datetime.now(UTC) - timedelta(days=120), path=alt,
            ),
            PageviewModel(
                created_at=datetime.now(UTC) - timedelta(days=1), path=frisch,
            ),
        ])
        await session.commit()

    deleted = await purge(days=90)
    assert deleted >= 1, "Der Job muss mindestens den 120 Tage alten Eintrag löschen"

    async with async_session_factory() as session:
        result = await session.execute(
            select(PageviewModel.path).where(PageviewModel.path.in_([alt, frisch]))
        )
        verbleibend = {p for (p,) in result.all()}

    assert alt not in verbleibend, "Alter Eintrag (120 Tage) muss gelöscht sein"
    assert frisch in verbleibend, "Frischer Eintrag (1 Tag) darf nicht gelöscht werden"


@pytest.mark.asyncio
async def test_purge_mit_kurzer_frist_loescht_auch_junge():
    """Die Frist muss steuerbar sein — sonst ist der Job nicht testbar/justierbar."""
    tag = uuid.uuid4().hex[:8]
    pfad = f"/mittel-{tag}"

    async with async_session_factory() as session:
        session.add(PageviewModel(
            created_at=datetime.now(UTC) - timedelta(days=10), path=pfad,
        ))
        await session.commit()

    await purge(days=7)

    async with async_session_factory() as session:
        result = await session.execute(
            select(PageviewModel.path).where(PageviewModel.path == pfad)
        )
        assert result.first() is None
