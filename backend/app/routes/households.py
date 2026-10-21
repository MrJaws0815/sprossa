"""Household + Member API-Routen (Postgres-persistent)."""
from datetime import datetime, UTC
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.repositories.household import HouseholdRepository
from app.repositories.member import MemberRepository
from app.schemas.api import HouseholdCreate, HouseholdOut, MemberCreate, MemberOut

router = APIRouter(tags=["households"], dependencies=[Depends(get_current_user_id)])


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
    )
    return HouseholdOut(
        id=household.id,
        name=household.name,
        dietary_profile=household.dietary_profile or {},
        created_at=household.created_at,
    )


@router.get("/households/{hid}", response_model=HouseholdOut)
async def get_household(
    hid: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = HouseholdRepository(db)
    household = await repo.get(hid)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    return HouseholdOut(
        id=household.id,
        name=household.name,
        dietary_profile=household.dietary_profile or {},
        created_at=household.created_at,
    )


@router.post("/households/{hid}/members", response_model=MemberOut, status_code=201)
async def create_member(
    hid: UUID,
    body: MemberCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    hrepo = HouseholdRepository(db)
    household = await hrepo.get(hid)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

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
    hrepo = HouseholdRepository(db)
    household = await hrepo.get(hid)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

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
    hrepo = HouseholdRepository(db)
    household = await hrepo.get(hid)
    if not household:
        raise HTTPException(status_code=404)

    mrepo = MemberRepository(db)
    member = await mrepo.get(mid)
    if not member or member.household_id != hid:
        raise HTTPException(status_code=404)

    await mrepo.delete(mid)