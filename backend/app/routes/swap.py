"""Swap-Route – Rezept in einem Plan-Slot tauschen (Task 32)."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.services.swap_service import swap_slot_recipe

router = APIRouter(tags=["swap"])


class SwapRequest(BaseModel):
    """Optionaler Body: ohne recipe_id wählt der Server automatisch."""
    recipe_id: Optional[UUID] = None


@router.post("/plans/{plan_id}/slots/{slot_id}/swap")
async def swap_slot(
    plan_id: UUID,
    slot_id: UUID,
    body: Optional[SwapRequest] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Tauscht das Rezept eines MealSlots.

    - `recipe_id` optional: ohne Angabe wird serverseitig ein passendes
      alternatives Rezept gewählt.
    - Constraints (Ernährungsweise + Allergien) werden serverseitig geprüft.
    - 409, wenn kein passendes Rezept existiert (kein stiller Fallback).
    """
    return await swap_slot_recipe(
        db=db,
        user_id=user_id,
        plan_id=plan_id,
        slot_id=slot_id,
        requested_recipe_id=body.recipe_id if body else None,
    )
