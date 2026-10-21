"""Tests für Plan-Generator + Grocery-Engine mit DB-Anbindung.

Testet async generate_and_persist_monthly_plan und generate_and_persist_grocery_list
mit einer Postgres-Datenbank (erwartet laufende Instanz via docker-compose oder localhost:5432).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid
import pytest

from datetime import date
from app.services.plan_generator import (
    GeneratorConfig,
    generate_and_persist_monthly_plan,
    weeks_in_month,
)
from app.services.grocery_engine import generate_and_persist_grocery_list
from app.models.database import (
    MonthlyPlan, WeeklyPlan, MealSlot,
    GroceryList, GroceryItem,
    User, Household, Member,
    Recipe, RecipeIngredient, Ingredient,
)
from app.core.database import async_session_factory


@pytest.fixture
async def db():
    """Liefert eine saubere async DB-Session (mit Rollback am Ende)."""
    async with async_session_factory() as session:
        # In einer echten Testumgebung würden wir Tables erstellen
        # Hier nutzen wir die existierende DB
        yield session
        await session.rollback()


@pytest.fixture
async def demo_household(db):
    """Legt einen Demo-User + Household + Recipe + Ingredient an."""
    from app.core.auth import hash_password

    # User erstellen
    user = User(
        email="test-plan@e2e.de",
        password_hash=hash_password("test1234"),
        display_name="Test Plan Familie",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Household erstellen
    household = Household(name="Test-Plan-Haushalt", user_id=user.id)
    db.add(household)
    await db.flush()
    await db.refresh(household)

    # Zutaten erstellen
    ingredients = []
    for name, cat in [("Karotten", "vegetables"), ("Kartoffeln", "vegetables"),
                       ("Hähnchenbrust", "meat"), ("Sahne", "dairy"),
                       ("Mehl", "grains"), ("Butter", "dairy")]:
        ing = Ingredient(name=name, category=cat, unit_default="g")
        db.add(ing)
        ingredients.append(ing)
    await db.flush()
    for ing in ingredients:
        await db.refresh(ing)

    # Rezepte mit Zutaten erstellen
    recipes = []
    for i in range(6):
        recipe = Recipe(
            household_id=household.id,
            title=f"Testrezept {i+1}",
            servings=4,
            cook_once_eat_twice=(i < 2),  # Erste 2 sind CookOnce
        )
        db.add(recipe)
        await db.flush()
        await db.refresh(recipe)

        # Jedes Rezept bekommt 2 Zutaten
        for j in range(2):
            idx = (i * 2 + j) % len(ingredients)
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredients[idx].id,
                quantity=200.0 if j == 0 else 100.0,
                unit="g" if j == 0 else "ml",
            )
            db.add(ri)

        recipes.append(recipe)
    await db.flush()

    yield {
        "user": user,
        "household": household,
        "recipes": recipes,
        "ingredients": ingredients,
    }

    # Cleanup
    await db.execute("DELETE FROM recipe_ingredients")
    await db.execute("DELETE FROM recipes")
    await db.execute("DELETE FROM ingredients")
    await db.execute("DELETE FROM members")
    await db.execute("DELETE FROM households")
    await db.execute("DELETE FROM users")


@pytest.mark.asyncio
async def test_generate_plan_aus_db_rezepten(db, demo_household):
    """Task 11: Ein Plan wird aus DB-Rezepten generiert und persistiert.

    Der Generator lädt Rezepte aus der DB (RecipeRepository.get_all()),
    erzeugt WeeklyPlans + MealSlots und schreibt alles in die Datenbank.
    """
    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        focus_tags=["schnell"],
    )

    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.commit()
    await db.refresh(monthly)

    # Verify: MonthlyPlan existiert in DB
    assert monthly.id is not None
    assert monthly.household_id == demo_household["household"].id
    assert monthly.month == 6
    assert monthly.year == 2026
    assert monthly.status == "draft"

    # Verify: WeeklyPlans wurden angelegt
    assert monthly.weekly_plans is not None
    assert len(monthly.weekly_plans) in (4, 5)  # Juni 2026 hat 5 Wochen

    # Verify: MealSlots existieren
    num_weeks = weeks_in_month(6, 2026)
    assert len(monthly.weekly_plans) == num_weeks

    total_slots = sum(len(wp.meal_slots) for wp in monthly.weekly_plans)
    assert total_slots > 7  # Mindestens 7 Dinner-Slots

    # Verify: Recipe-IDs in Slots sind echte DB-Rezepte
    recipe_ids_in_db = {r.id for r in demo_household["recipes"]}
    for wp in monthly.weekly_plans:
        for slot in (wp.meal_slots or []):
            assert slot.recipe_id in recipe_ids_in_db, (
                f"Slot recipe_id {slot.recipe_id} nicht in DB-Rezepten"
            )


@pytest.mark.asyncio
async def test_grocery_list_aus_weekly_plan(db, demo_household):
    """Task 12: Aus einem generierten WeeklyPlan eine Einkaufsliste erzeugen.

    generate_and_persist_grocery_list aggregiert Zutaten aus DB-Rezepten,
    respektiert CookOnce und schreibt GroceryList + GroceryItems in die DB.
    """
    # Zuerst einen Plan generieren
    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )

    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    # Den ersten WeeklyPlan nehmen
    weekly = monthly.weekly_plans[0]

    # Einkaufsliste generieren
    grocery = await generate_and_persist_grocery_list(
        weekly, db,
        household_id=demo_household["household"].id,
        monthly_plan_id=monthly.id,
        week_number=weekly.week_number,
    )
    await db.commit()
    await db.refresh(grocery)

    # Verify: GroceryList existiert
    assert grocery.id is not None
    assert grocery.household_id == demo_household["household"].id
    assert grocery.monthly_plan_id == monthly.id
    assert grocery.week_number == weekly.week_number

    # Verify: GroceryItems wurden angelegt
    items = grocery.items
    assert len(items) > 0, "Einkaufsliste sollte Items enthalten"

    # Verify: CookOnce-Rezepte tauchen nicht doppelt auf
    # (Die CookOnce-Rezepte haben eine Repeat-Slot, die ignoriert wird)
    # Prüfen: Keine doppelten Ingredient-IDs
    ingredient_ids = [item.ingredient_id for item in items]
    assert len(ingredient_ids) == len(set(ingredient_ids)), (
        "Keine doppelten Zutaten in der Einkaufsliste"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x", "--asyncio-mode=auto"])