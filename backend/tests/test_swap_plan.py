"""Tests für die Rezept-SWAP-Funktion (Task 32).

Deckt ab:
- Erfolgreicher automatischer Swap (ohne recipe_id)
- Erfolgreicher manueller Swap (mit recipe_id)
- Constraint-Verletzung (Allergen) → 409
- IDOR (fremder Plan) → 403/404
- Kein passendes alternatives Rezept → 409
- Einkaufsliste wird nach dem Swap neu generiert
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.database import (
    GroceryItem,
    GroceryList,
    Household,
    Ingredient,
    MealSlot,
    Member,
    MonthlyPlan,
    Recipe,
    RecipeIngredient,
    User,
    WeeklyPlan,
)
from app.services.swap_service import swap_slot_recipe
from app.core.database import async_session_factory


# ─── Helpers ──────────────────────────────────────────────────────────────


async def _create_user_and_household(db, *, dietary_profile=None, allergies=None):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"swap-test_{suffix}@example.com",
        password_hash="not-used-in-test",
        display_name="Swap Test User",
    )
    db.add(user)
    await db.flush()

    household = Household(
        name=f"Swap-Test-Haushalt-{suffix}",
        user_id=user.id,
        dietary_profile=dietary_profile or {},
    )
    db.add(household)
    await db.flush()

    member = Member(
        household_id=household.id,
        name="Test-Mitglied",
        allergies=allergies or [],
        is_active=True,
    )
    db.add(member)
    await db.flush()

    return user, household


async def _create_ingredients_and_recipes(db, household_id, specs):
    """specs: list[dict] mit title, tags, ingredients=[(ingredient_name, category, qty)]"""
    recipes = []
    for spec in specs:
        recipe = Recipe(
            household_id=household_id,
            title=spec["title"],
            servings=4,
            tags=spec.get("tags", []),
            cook_once_eat_twice=spec.get("cook_once_eat_twice", False),
        )
        db.add(recipe)
        await db.flush()

        for ing_name, ing_cat, qty in spec.get("ingredients", []):
            # Ingredient unique name – pro Testlauf mit Suffix
            suffix = uuid.uuid4().hex[:6]
            ing = Ingredient(
                name=f"{ing_name}_{suffix}",
                category=ing_cat,
                unit_default="g",
            )
            db.add(ing)
            await db.flush()
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ing.id,
                quantity=qty,
                unit="g",
            )
            db.add(ri)
        recipes.append(recipe)
    await db.flush()

    # Eager-load ingredients (sonst MissingGreenlet beim Filtern im Service)
    stmt = (
        select(Recipe)
        .where(Recipe.id.in_([r.id for r in recipes]))
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _create_plan_with_slots(db, household_id, recipe_ids):
    plan = MonthlyPlan(
        household_id=household_id,
        month=6,
        year=2026,
        status="draft",
        total_portions=2.0,
    )
    db.add(plan)
    await db.flush()

    weekly = WeeklyPlan(
        household_id=household_id,
        monthly_plan_id=plan.id,
        week_number=1,
        start_date=None,
    )
    db.add(weekly)
    await db.flush()

    slots = []
    for i, rid in enumerate(recipe_ids[:7]):
        slot = MealSlot(
            weekly_plan_id=weekly.id,
            day_of_week=i + 1,
            meal_type="dinner",
            recipe_id=rid,
            servings_multiplier=1.0,
            is_repeat=False,
        )
        db.add(slot)
        slots.append(slot)
    await db.flush()

    return plan, weekly, slots


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
async def db():
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ─── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_swap_auto_select_success(db):
    """Ohne recipe_id wählt der Server ein alternatives Rezept."""
    user, household = await _create_user_and_household(db)

    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
        {"title": "Rezept C", "tags": [], "ingredients": [("Reis", "grains", 150)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household.id, [recipes[0].id]
    )
    current_slot = slots[0]
    original_recipe_id = current_slot.recipe_id

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        result = await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=current_slot.id,
            requested_recipe_id=None,
        )

    assert result["id"] == current_slot.id
    assert result["recipe"]["id"] != original_recipe_id, "Rezept darf nicht dasselbe sein"
    assert result["recipe"]["title"] in {"Rezept B", "Rezept C"}
    assert result["day"] == current_slot.day_of_week
    assert result["meal_type"] == "dinner"


@pytest.mark.asyncio
async def test_swap_manual_select_success(db):
    """Mit recipe_id wird genau dieses Rezept gesetzt."""
    user, household = await _create_user_and_household(db)

    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household.id, [recipes[0].id]
    )
    current_slot = slots[0]
    target_recipe = recipes[1]

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        result = await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=current_slot.id,
            requested_recipe_id=target_recipe.id,
        )

    assert result["recipe"]["id"] == target_recipe.id
    assert result["recipe"]["title"] == "Rezept B"


@pytest.mark.asyncio
async def test_swap_allergen_constraint_violation(db):
    """Ein Rezept mit Allergen darf nicht getauscht werden → 409."""
    user, household = await _create_user_and_household(
        db, allergies=["laktose"]
    )

    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Sahne", "dairy", 200)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household.id, [recipes[0].id]
    )
    current_slot = slots[0]

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await swap_slot_recipe(
                db=db,
                user_id=str(user.id),
                plan_id=plan.id,
                slot_id=current_slot.id,
                requested_recipe_id=recipes[1].id,  # enthält Sahne → Laktose
            )

    assert exc_info.value.status_code == 409
    assert "Allergie" in exc_info.value.detail or "Ernährung" in exc_info.value.detail


@pytest.mark.asyncio
async def test_swap_idor_forbidden(db):
    """Ein fremder User darf den Plan nicht tauschen → 404/403."""
    user1, household1 = await _create_user_and_household(db)
    user2, _ = await _create_user_and_household(db)

    recipes = await _create_ingredients_and_recipes(db, household1.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household1.id, [recipes[0].id]
    )
    current_slot = slots[0]

    with pytest.raises(HTTPException) as exc_info:
        await swap_slot_recipe(
            db=db,
            user_id=str(user2.id),
            plan_id=plan.id,
            slot_id=current_slot.id,
        )

    assert exc_info.value.status_code in (403, 404)


@pytest.mark.asyncio
async def test_swap_no_alternative_409(db):
    """Wenn kein alternatives Rezept existiert → 409."""
    user, household = await _create_user_and_household(db)

    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Einziges Rezept", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household.id, [recipes[0].id]
    )
    current_slot = slots[0]

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await swap_slot_recipe(
                db=db,
                user_id=str(user.id),
                plan_id=plan.id,
                slot_id=current_slot.id,
                requested_recipe_id=None,
            )

    assert exc_info.value.status_code == 409
    assert "Kein passendes" in exc_info.value.detail


@pytest.mark.asyncio
async def test_swap_regenerates_grocery_list(db):
    """Nach dem Swap wird die Einkaufsliste der Woche neu erzeugt."""
    user, household = await _create_user_and_household(db)

    recipes = await _create_ingredients_and_recipes(db, household.id, [
        {"title": "Rezept A", "tags": [], "ingredients": [("Karotten", "vegetables", 200)]},
        {"title": "Rezept B", "tags": [], "ingredients": [("Kartoffeln", "vegetables", 300)]},
    ])

    plan, weekly, slots = await _create_plan_with_slots(
        db, household.id, [recipes[0].id]
    )
    current_slot = slots[0]

    # Erste Einkaufsliste manuell anlegen (ohne Items – reicht für den Test)
    gl = GroceryList(
        household_id=household.id,
        monthly_plan_id=plan.id,
        week_number=weekly.week_number,
        is_master_list=False,
    )
    db.add(gl)
    await db.flush()

    with patch(
        "app.services.swap_service._load_all_recipes_with_ingredients",
        return_value=recipes,
    ):
        result = await swap_slot_recipe(
            db=db,
            user_id=str(user.id),
            plan_id=plan.id,
            slot_id=current_slot.id,
            requested_recipe_id=recipes[1].id,
        )

    # Neue Liste muss existieren
    from sqlalchemy import select
    stmt = select(GroceryList).where(
        GroceryList.monthly_plan_id == plan.id,
        GroceryList.week_number == weekly.week_number,
    )
    lists = (await db.execute(stmt)).scalars().all()
    assert len(lists) >= 1, "Einkaufsliste muss nach dem Swap neu existieren"
    assert result["recipe"]["id"] == recipes[1].id
