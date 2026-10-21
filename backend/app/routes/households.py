"""Household + Member API-Routen (In-Memory-Store, später DB)"""
from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user_id
from app.schemas.api import HouseholdCreate, HouseholdOut, MemberCreate, MemberOut

router = APIRouter(tags=["households"], dependencies=[Depends(get_current_user_id)])

# In-Memory (wird durch DB ersetzt)
_HOUSEHOLDS: dict[str, dict] = {}
_MEMBERS: dict[str, dict] = {}


@router.post("/households", response_model=HouseholdOut, status_code=201)
async def create_household(body: HouseholdCreate, user_id: str = Depends(get_current_user_id)):
    hid = str(uuid4())
    _HOUSEHOLDS[hid] = {
        "id": hid,
        "name": body.name,
        "dietary_profile": body.dietary_profile or {},
        "user_id": user_id,
        "created_at": datetime.now(UTC),
    }
    return HouseholdOut(id=UUID(hid), name=body.name, dietary_profile=body.dietary_profile, created_at=_HOUSEHOLDS[hid]["created_at"])


@router.get("/households/{hid}", response_model=HouseholdOut)
async def get_household(hid: str, user_id: str = Depends(get_current_user_id)):
    h = _HOUSEHOLDS.get(hid)
    if not h:
        raise HTTPException(status_code=404, detail="Household not found")
    return HouseholdOut(id=UUID(hid), name=h["name"], dietary_profile=h["dietary_profile"], created_at=h["created_at"])


@router.post("/households/{hid}/members", response_model=MemberOut, status_code=201)
async def create_member(hid: str, body: MemberCreate, user_id: str = Depends(get_current_user_id)):
    if hid not in _HOUSEHOLDS:
        raise HTTPException(status_code=404, detail="Household not found")
    mid = str(uuid4())
    _MEMBERS[mid] = {
        "id": mid,
        "household_id": hid,
        "name": body.name,
        "age": body.age,
        "weight_kg": body.weight_kg,
        "allergies": body.allergies or [],
        "dietary_goals": body.dietary_goals or {},
        "notes": body.notes,
        "is_active": body.is_active,
    }
    return MemberOut(
        id=UUID(mid), household_id=UUID(hid), name=body.name,
        age=body.age, weight_kg=body.weight_kg,
        allergies=body.allergies or [],
        dietary_goals=body.dietary_goals or {},
        notes=body.notes, is_active=body.is_active,
    )


@router.get("/households/{hid}/members", response_model=list[MemberOut])
async def list_members(hid: str, user_id: str = Depends(get_current_user_id)):
    if hid not in _HOUSEHOLDS:
        raise HTTPException(status_code=404, detail="Household not found")
    members = [m for m in _MEMBERS.values() if m["household_id"] == hid]
    return [MemberOut(id=UUID(m["id"]), household_id=UUID(hid), name=m["name"], age=m["age"], weight_kg=m["weight_kg"], allergies=m["allergies"], dietary_goals=m["dietary_goals"], notes=m["notes"], is_active=m["is_active"]) for m in members]


@router.delete("/households/{hid}/members/{mid}", status_code=204)
async def delete_member(hid: str, mid: str, user_id: str = Depends(get_current_user_id)):
    if hid not in _HOUSEHOLDS:
        raise HTTPException(status_code=404)
    if mid not in _MEMBERS:
        raise HTTPException(status_code=404)
    del _MEMBERS[mid]