"""Zentrale Ownership-Prüfungen (Multi-Tenancy-Schutz).

Verhindert IDOR: jeder Zugriff auf Haushalt-/Plan-/Einkaufslisten-Daten
muss gegen die Haushalte des angemeldeten Users geprüft werden.
"""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.household import HouseholdRepository


async def get_user_households(db: AsyncSession, user_id: str):
    """Alle Haushalte, deren Owner der User ist."""
    repo = HouseholdRepository(db)
    return await repo.get_by_owner(UUID(user_id))


async def require_household(db: AsyncSession, user_id: str, hid: UUID | None = None):
    """Gibt den Haushalt zurück, wenn er dem User gehört — sonst 403/404.

    Ohne hid: erster Haushalt des Users (404, wenn keiner existiert).
    """
    households = await get_user_households(db, user_id)
    if not households:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kein Haushalt für diesen User gefunden – bitte zuerst einen Haushalt anlegen.",
        )
    if hid is None:
        return households[0]
    for h in households:
        if h.id == hid:
            return h
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Kein Zugriff auf diesen Haushalt.",
    )


async def require_household_id(db: AsyncSession, user_id: str) -> UUID:
    """ID des (ersten) Haushalts des Users."""
    h = await require_household(db, user_id)
    return h.id


async def require_plan_owner(db: AsyncSession, user_id: str, plan):
    """Prüft, ob ein Monatsplan zu einem Haushalt des Users gehört."""
    households = await get_user_households(db, user_id)
    hh_ids = {h.id for h in households}
    if plan is None or plan.household_id not in hh_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


async def require_weekly_plan_owner(db: AsyncSession, user_id: str, weekly):
    """Prüft, ob ein Wochenplan zu einem Haushalt des Users gehört."""
    households = await get_user_households(db, user_id)
    hh_ids = {h.id for h in households}
    if weekly is None or weekly.household_id not in hh_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WeeklyPlan not found")
    return weekly


async def require_grocery_owner(db: AsyncSession, user_id: str, gl):
    """Prüft, ob eine Einkaufsliste zu einem Haushalt des Users gehört."""
    households = await get_user_households(db, user_id)
    hh_ids = {h.id for h in households}
    if gl is None or gl.household_id not in hh_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GroceryList not found")
    return gl
