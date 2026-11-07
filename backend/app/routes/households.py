"""Household + Member API-Routen (Postgres-persistent)."""
import logging
from datetime import datetime, UTC
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.ownership import require_household, get_user_households
from app.repositories.household import HouseholdRepository
from app.repositories.member import MemberRepository
from app.schemas.api import HouseholdCreate, HouseholdOut, HouseholdUpdate, MemberCreate, MemberOut

# Kein router-level dependency: sync-Dep vor async DB-Writes verursacht MissingGreenlet.
# Jede Route deklariert get_current_user_id selbst.
router = APIRouter(tags=["households"])
logger = logging.getLogger(__name__)


@router.post("/households", response_model=HouseholdOut, status_code=201)
async def create_household(
    body: HouseholdCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    household = await repo.create(
        name=body.name,
        user_id=UUID(user_id),
        dietary_profile=body.dietary_profile or {},
        # Art. 9 DSGVO: Zeitstempel nur setzen, wenn Einwilligung erteilt wurde.
        health_data_consent_at=datetime.now(UTC) if body.health_data_consent else None,
    )
    return HouseholdOut(
        id=household.id,
        name=household.name,
        dietary_profile=household.dietary_profile or {},
        health_data_consent_at=household.health_data_consent_at,
        created_at=household.created_at,
    )


@router.put("/households/{hid}", response_model=HouseholdOut)
async def update_household(
    hid: UUID,
    body: HouseholdUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Aktualisiert einen Household (Name, Dietary-Profile)."""
    repo = HouseholdRepository(db)
    household = await require_household(db, user_id, hid)  # IDOR-Schutz

    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.dietary_profile is not None:
        updates["dietary_profile"] = body.dietary_profile
    # Art. 9 DSGVO: Einwilligung setzen (Zeitstempel nur beim ersten Mal) bzw. widerrufen.
    if body.health_data_consent is True and household.health_data_consent_at is None:
        updates["health_data_consent_at"] = datetime.now(UTC)
    if body.health_data_consent_revoked is True:
        # Widerruf nach Art. 7 Abs. 3 DSGVO: Die Einwilligung entfällt, damit
        # auch die Rechtsgrundlage für die Verarbeitung der Gesundheitsdaten.
        # Der Nachweis des Widerrufs bleibt, die Daten selbst müssen weg.
        dp = dict(household.dietary_profile or {})
        dp["health_data_consent_revoked_at"] = datetime.now(UTC).isoformat()
        dp.pop("allergies", None)
        updates["dietary_profile"] = dp
        # Allergien aller Mitglieder tatsächlich löschen. Vorher wurde nur
        # ein Zeitstempel gesetzt - die Allergien blieben gespeichert, obwohl
        # die Datenschutzerklärung Löschung zusagt.
        geloescht = await MemberRepository(db).clear_allergies(hid)
        if geloescht:
            logger.info("Widerruf Art. 9: Allergien von %s Mitgliedern gelöscht", geloescht)

    if updates:
        updated = await repo.update(hid, **updates)
        if updated is None:
            raise HTTPException(status_code=404, detail="Haushalt nicht gefunden")
        household = updated

    return HouseholdOut(
        id=household.id,
        name=household.name,
        dietary_profile=household.dietary_profile or {},
        health_data_consent_at=household.health_data_consent_at,
        created_at=household.created_at,
    )


@router.get("/households", response_model=list[HouseholdOut])
async def list_households(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet alle Households des aktuellen Users."""
    households = await get_user_households(db, user_id)
    return [
        HouseholdOut(
            id=h.id,
            name=h.name,
            dietary_profile=h.dietary_profile or {},
            health_data_consent_at=h.health_data_consent_at,
            created_at=h.created_at,
        )
        for h in households
    ]


@router.get("/households/{hid}", response_model=HouseholdOut)
async def get_household(
    hid: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    household = await require_household(db, user_id, hid)  # IDOR-Schutz
    return HouseholdOut(
        id=household.id,
        name=household.name,
        dietary_profile=household.dietary_profile or {},
        health_data_consent_at=household.health_data_consent_at,
        created_at=household.created_at,
    )


@router.post("/households/{hid}/members", response_model=MemberOut, status_code=201)
async def create_member(
    hid: UUID,
    body: MemberCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    household = await require_household(db, user_id, hid)  # IDOR-Schutz

    mrepo = MemberRepository(db)
    member = await mrepo.create(
        household_id=hid,
        name=body.name,
        age=body.age,
        weight_kg=body.weight_kg,
        allergies=body.allergies or [],
        dietary_goals=body.dietary_goals or {},
        notes=body.notes,
        is_active=body.is_active,
    )
    return MemberOut(
        id=member.id,
        household_id=member.household_id,
        name=member.name,
        age=member.age,
        weight_kg=member.weight_kg,
        allergies=member.allergies or [],
        dietary_goals=member.dietary_goals or {},
        notes=member.notes,
        is_active=member.is_active,
    )


@router.get("/households/{hid}/members", response_model=list[MemberOut])
async def list_members(
    hid: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    household = await require_household(db, user_id, hid)  # IDOR-Schutz

    mrepo = MemberRepository(db)
    members = await mrepo.get_by_household(hid)
    return [
        MemberOut(
            id=m.id,
            household_id=m.household_id,
            name=m.name,
            age=m.age,
            weight_kg=m.weight_kg,
            allergies=m.allergies or [],
            dietary_goals=m.dietary_goals or {},
            notes=m.notes,
            is_active=m.is_active,
        )
        for m in members
    ]


@router.delete("/households/{hid}/members/{mid}", status_code=204)
async def delete_member(
    hid: UUID,
    mid: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    household = await require_household(db, user_id, hid)  # IDOR-Schutz

    mrepo = MemberRepository(db)
    member = await mrepo.get(mid)
    if not member or member.household_id != hid:
        raise HTTPException(status_code=404)

    await mrepo.delete(mid)