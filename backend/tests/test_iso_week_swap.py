"""Tests für ISO-Kalenderwochen-Konsistenz beim Swap (Task 74/75).

Prüft, dass nach einem Swap die GroceryList.week_number aus dem Slot-Datum
per date.isocalendar() neu berechnet wird – inklusive Jahreswechsel.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select

from tests.test_swap_plan import (
    _create_user_and_household,
    _create_ingredients_and_recipes,
)
from app.models.database import GroceryList, MealSlot, MonthlyPlan, WeeklyPlan
from app.services.swap_service import swap_slot_recipe
from app.core.database import async_session_factory


@pytest.fixture
async def db():
    async with async_session_factory() as session:
        yield session
        await session.rollback()


async def _create_plan_with_weekly_date(
    db, household_id, recipe_ids, start_date: date, day_of_week: int
):
    """Erzeugt einen MonthlyPlan + WeeklyPlan mit konkretem Startdatum + Slot."""
    plan = MonthlyPlan(
        household_id=household_id,
        month=start_date.month,
        year=start_date.year,
        status="draft",
        total_portions=2.0,
    )
    db.add(plan)
    await db.flush()

    weekly = WeeklyPlan(
        household_id=household_id,
        monthly_plan_id=plan.id,
        week_number=1,  # interner Zähler – wird beim Swap NICHT überschrieben
        start_date=start_date,
    )
    db.add(weekly)
    await db.flush()

    slot = MealSlot(
        weekly_plan_id=weekly.id,
        day_of_week=day_of_week,
        meal_type="dinner",
        recipe_id=recipe_ids[0],
        servings_multiplier=1.0,
        is_repeat=False,
    )
    db.add(slot)
    await db.flush()

    return plan, weekly, slot


@pytest.mark.asyncio
async def test_swap_iso_week_december_2026(db):
    """Datum 2026-12-28 -> KW 53 (2026 hat 53 ISO-Wochen)."""
    user, household = await _create_user_and_household(db)
    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])
    start_date = date(2026, 12, 28)
    plan, weekly, slot = await _create_plan_with_weekly_date(
        db, household.id, [r.id for r in recipes], start_date, day_of_week=1
    )

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=slot.id,
            requested_recipe_id=recipes[1].id,
        )

    gl = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == plan.id)
        )
    ).scalars().first()
    assert gl is not None
    assert gl.week_number == 53


@pytest.mark.asyncio
async def test_swap_iso_week_january_2027(db):
    """Datum 2027-01-04 -> KW 1 (ISO-Jahr 2027)."""
    user, household = await _create_user_and_household(db)
    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])
    start_date = date(2027, 1, 4)
    plan, weekly, slot = await _create_plan_with_weekly_date(
        db, household.id, [r.id for r in recipes], start_date, day_of_week=1
    )

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=slot.id,
            requested_recipe_id=recipes[1].id,
        )

    gl = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == plan.id)
        )
    ).scalars().first()
    assert gl is not None
    assert gl.week_number == 1


@pytest.mark.asyncio
async def test_swap_iso_week_january_1_2027_is_week_53(db):
    """Datum 2027-01-01 (Freitag) -> KW 53 des ISO-Jahres 2026."""
    user, household = await _create_user_and_household(db)
    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])
    # Woche beginnt am Montag 28.12.2026; der Slot am Freitag ist der 01.01.2027.
    start_date = date(2026, 12, 28)
    plan, weekly, slot = await _create_plan_with_weekly_date(
        db, household.id, [r.id for r in recipes], start_date, day_of_week=5
    )

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=slot.id,
            requested_recipe_id=recipes[1].id,
        )

    gl = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == plan.id)
        )
    ).scalars().first()
    assert gl is not None
    assert gl.week_number == 53
