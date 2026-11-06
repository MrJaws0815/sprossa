"""Tests für ISO-Kalenderwoche + ISO-Jahr auf Einkaufslisten (Task 74/75).

Task 74: Der Swap-Pfad muss dieselbe KW erzeugen wie der Generator
         (start_date.isocalendar()), nicht den internen Zähler (1..5) und
         nicht das Slot-Datum.
Task 75: GroceryListOut liefert iso_year, damit KW 1 aus 2026 und KW 1 aus
         2027 unterscheidbar sind – in ALLEN Handlern (Liste + Einzelabruf).
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.database import GroceryList, MonthlyPlan, WeeklyPlan
from app.routes.family import get_grocery_list, list_grocery_lists
from app.schemas.api import GroceryListOut
from app.services.grocery_engine import iso_year_week
from app.services.swap_service import swap_slot_recipe
from tests.test_swap_plan import (
    _create_ingredients_and_recipes,
    _create_user_and_household,
)


@pytest.fixture
async def db():
    async with async_session_factory() as session:
        yield session
        await session.rollback()


async def _create_plan_week_and_list(
    db, household_id, *, year: int, month: int, start_date, week_number: int,
    internal_week: int = 1,
):
    """Legt Monatsplan + Wochenplan + Einkaufsliste mit ISO-KW an."""
    plan = MonthlyPlan(
        household_id=household_id,
        month=month,
        year=year,
        status="draft",
        total_portions=2.0,
    )
    db.add(plan)
    await db.flush()

    weekly = WeeklyPlan(
        household_id=household_id,
        monthly_plan_id=plan.id,
        week_number=internal_week,
        start_date=start_date,
    )
    db.add(weekly)
    await db.flush()

    grocery_list = GroceryList(
        household_id=household_id,
        monthly_plan_id=plan.id,
        week_number=week_number,
        is_master_list=False,
    )
    db.add(grocery_list)
    await db.flush()
    return plan, weekly, grocery_list


# ─── Task 75: iso_year in beiden Handlern ────────────────────────────────


@pytest.mark.asyncio
async def test_list_handler_liefert_iso_year_je_liste(db):
    """KW 53/2026, KW 1/2027 und KW 1/2026 sind eindeutig unterscheidbar."""
    user, household = await _create_user_and_household(db)

    await _create_plan_week_and_list(
        db, household.id, year=2026, month=12,
        start_date=date(2026, 12, 28), week_number=53,
    )
    await _create_plan_week_and_list(
        db, household.id, year=2027, month=1,
        start_date=date(2027, 1, 4), week_number=1,
    )
    await _create_plan_week_and_list(
        db, household.id, year=2026, month=1,
        start_date=date(2025, 12, 29), week_number=1,
    )

    result = await list_grocery_lists(user_id=str(user.id), db=db)
    pairs = {(item.week_number, item.iso_year) for item in result}

    assert (53, 2026) in pairs
    assert (1, 2027) in pairs
    assert (1, 2026) in pairs
    # Die beiden KW-1-Listen dürfen NICHT denselben Schlüssel haben.
    kw1 = [item for item in result if item.week_number == 1]
    assert len({item.iso_year for item in kw1}) == 2


@pytest.mark.asyncio
async def test_single_handler_liefert_iso_year(db):
    """Einzelabruf setzt iso_year genauso wie die Liste (keine Divergenz)."""
    user, household = await _create_user_and_household(db)
    _plan, _weekly, grocery_list = await _create_plan_week_and_list(
        db, household.id, year=2026, month=12,
        start_date=date(2026, 12, 28), week_number=53,
    )

    out = await get_grocery_list(gl_id=grocery_list.id, user_id=str(user.id), db=db)

    assert out.week_number == 53
    assert out.iso_year == 2026
    assert out.id == grocery_list.id


@pytest.mark.asyncio
async def test_kw1_aus_zwei_jahren_erzeugt_keine_falschen_segmente(db):
    """Zwei KW-1-Listen aus 2026 und 2027 sind keine Einkaufstage-Segmente."""
    user, household = await _create_user_and_household(db)

    await _create_plan_week_and_list(
        db, household.id, year=2027, month=1,
        start_date=date(2027, 1, 4), week_number=1,
    )
    await _create_plan_week_and_list(
        db, household.id, year=2026, month=1,
        start_date=date(2025, 12, 29), week_number=1,
    )

    result = await list_grocery_lists(user_id=str(user.id), db=db)
    kw1 = [item for item in result if item.week_number == 1]

    assert len(kw1) == 2
    assert all(item.segment_label is None for item in kw1)


@pytest.mark.asyncio
async def test_master_liste_hat_kein_iso_year(db):
    """Monatsliste (week_number NULL) hat kein ISO-Jahr – kein geratenes Jahr."""
    user, household = await _create_user_and_household(db)
    plan, _weekly, _gl = await _create_plan_week_and_list(
        db, household.id, year=2026, month=12,
        start_date=date(2026, 12, 28), week_number=53,
    )
    master = GroceryList(
        household_id=household.id,
        monthly_plan_id=plan.id,
        week_number=None,
        is_master_list=True,
    )
    db.add(master)
    await db.flush()

    out = await get_grocery_list(gl_id=master.id, user_id=str(user.id), db=db)
    assert out.is_master_list is True
    assert out.iso_year is None


@pytest.mark.asyncio
async def test_ohne_startdatum_kein_iso_year(db):
    """Altbestand ohne Wochen-Startdatum: iso_year bleibt None (nicht geraten)."""
    user, household = await _create_user_and_household(db)
    _plan, _weekly, grocery_list = await _create_plan_week_and_list(
        db, household.id, year=2026, month=5,
        start_date=None, week_number=20,
    )

    out = await get_grocery_list(gl_id=grocery_list.id, user_id=str(user.id), db=db)
    assert out.week_number == 20
    assert out.iso_year is None


def test_grocery_list_out_serialisiert_iso_year():
    """Das Response-Schema enthält iso_year (Task 75)."""
    payload = GroceryListOut(
        id=uuid.uuid4(),
        week_number=1,
        cw=1,
        iso_year=2027,
        is_master_list=False,
        generated_at=datetime(2027, 1, 4, 10, 0, tzinfo=timezone.utc),
        items=[],
    )
    dumped = payload.model_dump()
    assert dumped["iso_year"] == 2027
    # Feld ist optional -> Default None, damit alte Clients nicht brechen.
    assert GroceryListOut.model_fields["iso_year"].default is None


def test_iso_year_week_jahreswechsel():
    """ISO-Jahr, nicht Kalenderjahr: 2027-01-01 gehört zu KW 53/2026."""
    assert iso_year_week(date(2027, 1, 1)) == (2026, 53)
    assert iso_year_week(date(2026, 12, 28)) == (2026, 53)
    assert iso_year_week(date(2027, 1, 4)) == (2027, 1)
    assert iso_year_week(None) == (None, None)


# ─── Task 74: Swap erzeugt die KW des Generators ─────────────────────────


@pytest.mark.asyncio
async def test_swap_nutzt_startdatum_nicht_slot_datum(db):
    """Woche beginnt am Do 31.12.2026; Slot an Tag 5 wäre Mo 04.01.2027 (KW 1).

    Der Generator labelt die Woche mit start_date -> KW 53/2026. Der Swap muss
    dieselbe KW schreiben, sonst entstehen beim Neugenerieren zwei Listen.
    """
    user, household = await _create_user_and_household(db)
    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])

    plan = MonthlyPlan(
        household_id=household.id, month=12, year=2026,
        status="draft", total_portions=2.0,
    )
    db.add(plan)
    await db.flush()

    weekly = WeeklyPlan(
        household_id=household.id,
        monthly_plan_id=plan.id,
        week_number=1,  # interner Zähler, NICHT die ISO-KW
        start_date=date(2026, 12, 31),
    )
    db.add(weekly)
    await db.flush()

    from app.models.database import MealSlot

    slot = MealSlot(
        weekly_plan_id=weekly.id,
        day_of_week=5,  # Do + 4 Tage = Mo 04.01.2027 (KW 1)
        meal_type="dinner",
        recipe_id=recipes[0].id,
        servings_multiplier=1.0,
        is_repeat=False,
    )
    db.add(slot)
    await db.flush()

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
    assert gl.week_number == 53   # ISO-KW aus start_date
    assert gl.week_number != 1    # nicht der interne Zähler
    # Gegenprobe: das Slot-Datum (Mo 04.01.2027) gehört zu KW 1 – der Swap
    # darf daraus NICHT die KW ableiten, sonst weicht er vom Generator ab.
    assert date(2027, 1, 4).isocalendar()[1] == 1


@pytest.mark.asyncio
async def test_swap_ohne_startdatum_faellt_auf_internen_zaehler_zurueck(db):
    """Altbestand ohne start_date: einzige Information ist der interne Zähler."""
    user, household = await _create_user_and_household(db)
    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])

    plan = MonthlyPlan(
        household_id=household.id, month=3, year=2026,
        status="draft", total_portions=2.0,
    )
    db.add(plan)
    await db.flush()

    weekly = WeeklyPlan(
        household_id=household.id,
        monthly_plan_id=plan.id,
        week_number=3,
        start_date=None,
    )
    db.add(weekly)
    await db.flush()

    from app.models.database import MealSlot

    slot = MealSlot(
        weekly_plan_id=weekly.id,
        day_of_week=2,
        meal_type="dinner",
        recipe_id=recipes[0].id,
        servings_multiplier=1.0,
        is_repeat=False,
    )
    db.add(slot)
    await db.flush()

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
    assert gl.week_number == 3
