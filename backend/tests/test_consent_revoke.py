"""Widerruf der Art.-9-Einwilligung muss die Gesundheitsdaten löschen.

Lücke 5 aus dem Rechtsseiten-Audit: Der Widerruf setzte nur einen Zeitstempel,
die Allergien blieben in der Datenbank. Die Datenschutzerklärung sagt aber
Löschung zu — und Art. 7 Abs. 3 DSGVO verlangt, dass nach dem Widerruf nicht
weiterverarbeitet wird.
"""
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.database import Household, Member, User
from app.routes.households import update_household
from app.schemas.api import HouseholdUpdate


@pytest.mark.asyncio
async def test_widerruf_loescht_allergien_aller_mitglieder():
    tag = uuid.uuid4().hex[:8]

    async with async_session_factory() as db:
        user = User(
            email=f"revoke_{tag}@example.com",
            password_hash="not-used-in-test",
            display_name="Widerruf Test",
        )
        db.add(user)
        await db.flush()

        household = Household(
            name=f"Widerruf-Haushalt-{tag}",
            user_id=user.id,
            dietary_profile={},
            health_data_consent_at=datetime.now(UTC),
        )
        db.add(household)
        await db.flush()

        db.add_all([
            Member(household_id=household.id, name="Kind", allergies=["nuesse", "gluten"], is_active=True),
            Member(household_id=household.id, name="Erwachsener", allergies=["laktose"], is_active=True),
            Member(household_id=household.id, name="Ohne Allergie", allergies=[], is_active=True),
        ])
        await db.commit()

        hid = household.id
        uid = str(user.id)

    # Widerruf über die Route. In der App committet die FastAPI-Dependency
    # get_db(); beim direkten Aufruf muss der Test selbst committen.
    async with async_session_factory() as db:
        await update_household(
            hid, HouseholdUpdate(health_data_consent_revoked=True), user_id=uid, db=db,
        )
        await db.commit()

    async with async_session_factory() as db:
        result = await db.execute(select(Member).where(Member.household_id == hid))
        members = result.scalars().all()

        assert len(members) == 3, "Mitglieder dürfen durch den Widerruf nicht verschwinden"
        for member in members:
            assert not member.allergies, (
                f"Allergien von '{member.name}' müssen nach dem Widerruf gelöscht sein: "
                f"{member.allergies}"
            )

        # Der Widerruf selbst muss dokumentiert bleiben.
        hh_result = await db.execute(select(Household).where(Household.id == hid))
        hh = hh_result.scalar_one()
        assert "health_data_consent_revoked_at" in (hh.dietary_profile or {}), (
            "Der Zeitpunkt des Widerrufs muss als Nachweis erhalten bleiben"
        )
