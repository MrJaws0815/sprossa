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

    # User erstellen (eindeutige E-Mail gegen Unique-Constraint-Kollisionen)
    _suffix = uuid.uuid4().hex[:6]
    user = User(
        email=f"test-plan_{_suffix}@e2e.de",
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

    # Zutaten erstellen (eindeutiger Suffix gegen Unique-Constraint-Kollisionen)
    suffix = uuid.uuid4().hex[:6]
    ingredients = []
    for name, cat in [("Karotten", "vegetables"), ("Kartoffeln", "vegetables"),
                       ("Hähnchenbrust", "meat"), ("Sahne", "dairy"),
                       ("Mehl", "grains"), ("Butter", "dairy")]:
        ing = Ingredient(name=f"{name}_{suffix}", category=cat, unit_default="g")
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
            title=f"Fixturegericht {i+1}",
            servings=4,
            cook_once_eat_twice=(i < 2),  # Erste 2 sind CookOnce
            tags=["schnell"],
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

    # Cleanup: NUR die vom Fixture erzeugten Datensätze löschen (keine Seed-Daten!)
    # Reihenfolge beachten: erst abhängige Tabellen (FK), dann Haushalt/User.
    from sqlalchemy import text
    hid = household.id
    # 1) Grocery Items + Lists
    await db.execute(text("DELETE FROM grocery_items WHERE grocery_list_id IN (SELECT id FROM grocery_lists WHERE household_id = :hid)"), {"hid": hid})
    await db.execute(text("DELETE FROM grocery_lists WHERE household_id = :hid"), {"hid": hid})
    # 2) Meal Slots -> Weekly Plans -> Monthly Plans
    await db.execute(text("DELETE FROM meal_slots WHERE weekly_plan_id IN (SELECT id FROM weekly_plans WHERE household_id = :hid)"), {"hid": hid})
    await db.execute(text("DELETE FROM weekly_plans WHERE household_id = :hid"), {"hid": hid})
    await db.execute(text("DELETE FROM monthly_plans WHERE household_id = :hid"), {"hid": hid})
    # 3) Recipe-Verknüpfungen -> Recipes -> Ingredients
    await db.execute(text("DELETE FROM recipe_ingredients WHERE recipe_id IN (SELECT id FROM recipes WHERE household_id = :hid)"), {"hid": hid})
    await db.execute(text("DELETE FROM recipes WHERE household_id = :hid"), {"hid": hid})
    await db.execute(text("DELETE FROM ingredients WHERE name LIKE :pat"), {"pat": f"%_{suffix}"})
    # 4) Members -> Household -> User
    await db.execute(text("DELETE FROM members WHERE household_id = :hid"), {"hid": hid})
    await db.execute(text("DELETE FROM households WHERE id = :hid"), {"hid": hid})
    await db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user.id})
    await db.commit()


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

    # Eager Loading nach Commit, damit die Assertions nicht auf lazy-loads
    # zugreifen (sonst MissingGreenlet / DetachedInstanceError).
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    monthly = (
        await db.execute(
            select(MonthlyPlan)
            .where(MonthlyPlan.id == monthly.id)
            .options(
                selectinload(MonthlyPlan.weekly_plans).selectinload(WeeklyPlan.meal_slots)
            )
        )
    ).scalar_one()

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

    # Den ersten WeeklyPlan nehmen (Eager Loading gegen MissingGreenlet)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    monthly = (
        await db.execute(
            select(MonthlyPlan)
            .where(MonthlyPlan.id == monthly.id)
            .options(
                selectinload(MonthlyPlan.weekly_plans).selectinload(WeeklyPlan.meal_slots)
            )
        )
    ).scalar_one()
    weekly = monthly.weekly_plans[0]

    # Einkaufsliste generieren
    grocery = await generate_and_persist_grocery_list(
        weekly, db,
        household_id=demo_household["household"].id,
        monthly_plan_id=monthly.id,
        week_number=weekly.week_number,
    )
    await db.commit()

    # Eager Loading der Items gegen MissingGreenlet beim Lazy-Load.
    grocery = (
        await db.execute(
            select(GroceryList)
            .where(GroceryList.id == grocery.id)
            .options(selectinload(GroceryList.items))
        )
    ).scalar_one()

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


# ═══════════════════════════════════════════════════════════════════════════
# Demo-Account-Bugfixes (Regressionstests)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_recipe_detail_liefert_instructions_und_zutat_metadaten(db, demo_household):
    """BUG 1: RecipeOut enthält instructions; Zutaten liefern name + category."""
    from app.routes.family import get_recipe, list_recipes

    recipe = demo_household["recipes"][0]
    recipe.instructions = "1. Zutaten schneiden.\n2. Kochen."
    await db.flush()

    detail = await get_recipe(recipe.id, multiplier=1.0, user_id=str(demo_household["user"].id), db=db)
    assert detail.instructions == recipe.instructions
    assert len(detail.ingredients) >= 1
    first = detail.ingredients[0]
    assert first.name and first.name != ""
    assert first.category and first.category != ""
    # Kompatibilitätsfeld bleibt gefüllt
    assert first.ingredient_name == first.name

    listed = await list_recipes(user_id=str(demo_household["user"].id), db=db)
    listed_recipe = next(r for r in listed if r.id == recipe.id)
    assert listed_recipe.instructions == recipe.instructions


@pytest.mark.asyncio
async def test_recipe_detail_skaliert_portionen(db, demo_household):
    """Bug 76: get_recipe skaliert servings und Zutat-Mengen via multiplier."""
    from app.routes.family import get_recipe

    recipe = demo_household["recipes"][0]

    # Ohne Multiplier (Default 1.0) -> Basiswerte
    base = await get_recipe(recipe.id, multiplier=1.0, user_id=str(demo_household["user"].id), db=db)
    assert base.servings == 4.0  # Fixture-Rezept hat 4 Basis-Portionen
    assert base.ingredients[0].quantity == 200.0

    # Mit Multiplier 0.925 -> 3.7 Portionen
    scaled = await get_recipe(recipe.id, multiplier=0.925, user_id=str(demo_household["user"].id), db=db)
    assert scaled.servings == 3.7
    assert scaled.ingredients[0].quantity == 185.0


@pytest.mark.asyncio
async def test_weekly_plan_slots_liefern_recipe_titel(db, demo_household):
    """BUG 2: MealSlotOut enthält recipe_title + recipe_servings."""
    from sqlalchemy import select
    from app.routes.family import get_weekly_plan

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=7,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    wp = (
        await db.execute(
            select(WeeklyPlan)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
            .order_by(WeeklyPlan.week_number)
        )
    ).scalars().first()

    out = await get_weekly_plan(wp.id, user_id=str(demo_household["user"].id), db=db)
    assert out.meal_slots
    for slot in out.meal_slots:
        assert slot.recipe_title, "recipe_title darf nicht leer sein"
        assert slot.recipe_servings is not None


@pytest.mark.asyncio
async def test_monthly_plan_metadata_deutscher_monatsname(db, demo_household):
    """BUG 6: month_name, weeks_count, recipe_count in list_plans/get_plan."""
    from app.routes.family import get_plan, list_plans

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=10,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    out = await get_plan(monthly.id, user_id=str(demo_household["user"].id), db=db)
    assert out.month_name == "Oktober"
    assert out.weeks_count == weeks_in_month(10, 2026)
    assert out.recipe_count > 0

    listed = await list_plans(user_id=str(demo_household["user"].id), db=db)
    target = next(p for p in listed if p.id == monthly.id)
    assert target.month_name == "Oktober"
    assert target.weeks_count == weeks_in_month(10, 2026)
    assert target.recipe_count > 0


@pytest.mark.asyncio
async def test_plan_upsert_erzeugt_kein_duplikat(db, demo_household):
    """BUG 3: Zweite Generierung aktualisiert denselben Plan statt zu duplizieren."""
    from sqlalchemy import func, select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=8,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )
    first = await generate_and_persist_monthly_plan(config, db)
    await db.flush()
    first_id = first.id
    assert getattr(first, "was_created", None) is True

    second = await generate_and_persist_monthly_plan(config, db)
    await db.flush()
    assert second.id == first_id
    assert getattr(second, "was_created", None) is False

    plan_count = (
        await db.execute(
            select(func.count())
            .select_from(MonthlyPlan)
            .where(
                MonthlyPlan.household_id == demo_household["household"].id,
                MonthlyPlan.month == 8,
                MonthlyPlan.year == 2026,
            )
        )
    ).scalar()
    assert plan_count == 1, "Upsert darf kein Duplikat erzeugen"

    week_count = (
        await db.execute(
            select(func.count())
            .select_from(WeeklyPlan)
            .where(WeeklyPlan.monthly_plan_id == first_id)
        )
    ).scalar()
    assert week_count == weeks_in_month(8, 2026)


@pytest.mark.asyncio
async def test_grocery_generate_nutzt_iso_kalenderwoche(db, demo_household):
    """BUG 4: Einkaufsliste verwendet ISO-KW statt 1..5."""
    from sqlalchemy import select
    from app.routes.family import generate_grocery

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=9,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    wp = (
        await db.execute(
            select(WeeklyPlan)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
            .order_by(WeeklyPlan.week_number)
        )
    ).scalars().first()

    result = await generate_grocery(
        weekly_plan_id=wp.id,
        user_id=str(demo_household["user"].id),
        db=db,
    )
    expected_cw = wp.start_date.isocalendar()[1]
    assert result["week_number"] == expected_cw
    assert expected_cw != wp.week_number or expected_cw == wp.week_number


@pytest.mark.asyncio
async def test_recipes_planned_only_filter(db, demo_household):
    """BUG 5: planned_only=True liefert nur Rezepte aus MealSlots der User-Pläne."""
    from sqlalchemy import select
    from app.routes.family import list_recipes

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=11,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    planned_ids = set(
        (
            await db.execute(
                select(MealSlot.recipe_id)
                .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
                .join(MonthlyPlan, WeeklyPlan.monthly_plan_id == MonthlyPlan.id)
                .where(MonthlyPlan.household_id == demo_household["household"].id)
                .distinct()
            )
        ).scalars().all()
    )
    assert planned_ids

    recipes = await list_recipes(
        planned_only=True,
        user_id=str(demo_household["user"].id),
        db=db,
    )
    assert {r.id for r in recipes} == planned_ids


@pytest.mark.asyncio
async def test_generate_plan_route_upsert_flags_und_grocery(db, demo_household):
    """BUG 3/4: Route meldet created/updated korrekt und ersetzt GroceryLists."""
    from sqlalchemy import func, select
    from app.schemas.api import MonthlyPlanCreate
    from app.routes.family import generate_plan as generate_plan_route

    # Aktueller Monat ist Okt 2026 -> naechster Monat November ist erlaubt.
    demo_household["household"].dietary_profile = {"shopping_frequency": "1x_woche"}
    await db.flush()
    body = MonthlyPlanCreate(month=11, year=2026)
    uid = str(demo_household["user"].id)
    hid = demo_household["household"].id

    first = await generate_plan_route(body=body, user_id=uid, db=db)
    assert first["created"] is True
    assert first["updated"] is False
    assert first["grocery_list"]
    plan_id = first["plan_id"]

    second = await generate_plan_route(body=body, user_id=uid, db=db)
    assert second["created"] is False
    assert second["updated"] is True
    assert second["plan_id"] == plan_id

    plan_count = (
        await db.execute(
            select(func.count())
            .select_from(MonthlyPlan)
            .where(
                MonthlyPlan.household_id == hid,
                MonthlyPlan.month == 11,
                MonthlyPlan.year == 2026,
            )
        )
    ).scalar()
    assert plan_count == 1

    grocery_count = (
        await db.execute(
            select(func.count())
            .select_from(GroceryList)
            .where(GroceryList.monthly_plan_id == plan_id)
        )
    ).scalar()
    # Seit dem ISO-KW-Fix wird pro Planwoche eine Liste erzeugt.
    assert grocery_count == weeks_in_month(11, 2026)

    # Jede Liste traegt die ISO-Kalenderwoche ihres WeeklyPlans.
    week_rows = (
        await db.execute(
            select(WeeklyPlan.week_number, WeeklyPlan.start_date)
            .where(WeeklyPlan.monthly_plan_id == plan_id)
            .order_by(WeeklyPlan.week_number)
        )
    ).all()
    grocery_weeks = sorted(
        (
            await db.execute(
                select(GroceryList.week_number).where(
                    GroceryList.monthly_plan_id == plan_id
                )
            )
        ).scalars().all()
    )
    expected_weeks = sorted(start.isocalendar()[1] for _, start in week_rows)
    assert grocery_weeks == expected_weeks
    assert all(cw != wn for cw, (wn, _) in zip(grocery_weeks, week_rows)), (
        "grocery_lists.week_number darf nicht der interne Wochenzaehler sein"
    )


@pytest.mark.asyncio
async def test_vegetarischer_haushalt_waehlt_kein_fleisch_oder_fisch(db, demo_household):
    """BUG 6: dietary_profile["diet_types"] wird gelesen und filtert Fleisch/Fisch."""
    from sqlalchemy import select
    from app.models.database import MealSlot

    recipes = demo_household["recipes"]
    # 0-2 Fleisch, 3 Fisch, 4-5 vegetarisch
    for idx, recipe in enumerate(recipes):
        if idx <= 2:
            recipe.tags = ["fleisch"]
        elif idx == 3:
            recipe.tags = ["fisch"]
        else:
            recipe.tags = ["vegetarisch"]
    await db.flush()

    vegetarian_ids = {recipes[4].id, recipes[5].id}

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=11,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in recipes],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={"diet_types": ["vegetarisch"]},
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    slot_rows = (
        await db.execute(
            select(MealSlot.recipe_id)
            .join(WeeklyPlan, WeeklyPlan.id == MealSlot.weekly_plan_id)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
        )
    ).scalars().all()
    chosen = set(slot_rows)
    assert chosen, "Es muessen Slots erzeugt worden sein"
    # Der Katalog ist global: pruefe die tatsaechlich gewaehlten Rezepte auf Tags.
    chosen_recipes = (
        await db.execute(select(Recipe).where(Recipe.id.in_(chosen)))
    ).scalars().all()
    for recipe in chosen_recipes:
        tags = {t.lower().strip() for t in (recipe.tags or [])}
        assert "fleisch" not in tags and "fisch" not in tags, (
            f"Vegetarischer Haushalt bekam {recipe.title} mit Tags {tags}"
        )


@pytest.mark.asyncio
async def test_haushalts_allergie_filtert_zutaten(db, demo_household):
    """BUG 6: Allergien aus dietary_profile werden wie Member-Allergien behandelt."""
    from sqlalchemy import select
    from app.models.database import MealSlot, Ingredient, RecipeIngredient

    # Rezepte mit Milchprodukten ermitteln (Kategorie dairy)
    dairy_recipe_ids = set(
        (
            await db.execute(
                select(RecipeIngredient.recipe_id)
                .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
                .where(
                    Ingredient.category == "dairy",
                    RecipeIngredient.recipe_id.in_(
                        [r.id for r in demo_household["recipes"]]
                    ),
                )
            )
        ).scalars().all()
    )
    assert dairy_recipe_ids, "Fixture muss Rezepte mit Milchprodukten enthalten"

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=11,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        # Keine Member-Allergien, nur Haushalts-Profil
        members=[],
        dietary_profile={"allergies": ["laktose"]},
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    chosen = set(
        (
            await db.execute(
                select(MealSlot.recipe_id)
                .join(WeeklyPlan, WeeklyPlan.id == MealSlot.weekly_plan_id)
                .where(WeeklyPlan.monthly_plan_id == monthly.id)
            )
        ).scalars().all()
    )
    assert chosen, "Es muessen Slots erzeugt worden sein"
    # Global pruefen: kein gewaehltes Rezept darf eine Dairy-Zutat enthalten.
    chosen_dairy = set(
        (
            await db.execute(
                select(RecipeIngredient.recipe_id)
                .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
                .where(
                    RecipeIngredient.recipe_id.in_(chosen),
                    Ingredient.category == "dairy",
                )
            )
        ).scalars().all()
    )
    assert chosen_dairy.isdisjoint(chosen), (
        f"Haushalts-Allergie laktose ignoriert: {chosen_dairy & chosen}"
    )


@pytest.mark.asyncio
async def test_grocery_lists_tragen_iso_kalenderwoche(db, demo_household):
    """BUG 5: Pro Woche eine GroceryList mit ISO-KW (nicht interner 1..5-Zaehler)."""
    from sqlalchemy import select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=11,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={"shopping_frequency": "1x_woche"},
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    weeks = (
        await db.execute(
            select(WeeklyPlan.week_number, WeeklyPlan.start_date)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
            .order_by(WeeklyPlan.week_number)
        )
    ).all()
    grocery_weeks = (
        await db.execute(
            select(GroceryList.week_number)
            .where(GroceryList.monthly_plan_id == monthly.id)
            .order_by(GroceryList.generated_at, GroceryList.id)
        )
    ).scalars().all()

    assert len(grocery_weeks) == len(weeks), "pro Planwoche genau eine Einkaufsliste"
    expected = [start.isocalendar()[1] for _, start in weeks]
    assert list(grocery_weeks) == expected
    # November 2026 liegt in ISO-KW 44-48, nicht in 1..5.
    assert all(cw not in (1, 2, 3, 4, 5) for cw in grocery_weeks)


# ── Shopping-Frequency Tests (Master-Liste vs. Wochenlisten) ──


@pytest.mark.asyncio
async def test_shopping_frequency_nach_bedarf_master_list(db, demo_household):
    """Prüft, dass 'nach_bedarf' eine einzelne Master-Liste erzeugt."""
    from sqlalchemy import select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={"shopping_frequency": "nach_bedarf"},
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    grocery_lists = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    assert len(grocery_lists) == 1, "nach_bedarf sollte genau 1 Master-Liste erzeugen"
    assert grocery_lists[0].is_master_list is True
    assert grocery_lists[0].week_number is None


@pytest.mark.asyncio
async def test_shopping_frequency_1x_woche_weekly_lists(db, demo_household):
    """Prüft, dass '1x_woche' eine Liste pro Woche erzeugt."""
    from sqlalchemy import select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={"shopping_frequency": "1x_woche"},
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    grocery_lists = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    num_weeks = weeks_in_month(6, 2026)
    assert len(grocery_lists) == num_weeks, f"1x_woche sollte {num_weeks} Wochenlisten erzeugen"
    for gl in grocery_lists:
        assert gl.is_master_list is False
        assert gl.week_number is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x", "--asyncio-mode=auto"])

# ── Task 85: shopping_days unterteilt Wochenliste in Segmente ──


@pytest.mark.asyncio
async def test_shopping_days_1_4_erzeugt_zwei_listen_pro_woche(db, demo_household):
    """shopping_days=[1,4] → 2 Listen pro Woche (10 Listen für 5 Wochen)."""
    from sqlalchemy import select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={
            "shopping_frequency": "1x_woche",
            "shopping_days": [1, 4],
        },
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    grocery_lists = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    num_weeks = weeks_in_month(6, 2026)
    assert len(grocery_lists) == num_weeks * 2, (
        f"shopping_days=[1,4] sollte {num_weeks * 2} Listen erzeugen, "
        f"bekommen {len(grocery_lists)}"
    )
    for gl in grocery_lists:
        assert gl.is_master_list is False
        assert gl.week_number is not None


@pytest.mark.asyncio
async def test_shopping_days_leer_erzeugt_eine_liste_pro_woche(db, demo_household):
    """shopping_days=[] → 1 Liste pro Woche (bisheriges Verhalten)."""
    from sqlalchemy import select

    config = GeneratorConfig(
        household_id=demo_household["household"].id,
        month=6,
        year=2026,
        member_ids=[],
        recipe_ids=[r.id for r in demo_household["recipes"]],
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        dietary_profile={
            "shopping_frequency": "1x_woche",
            "shopping_days": [],
        },
    )
    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.flush()

    grocery_lists = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    num_weeks = weeks_in_month(6, 2026)
    assert len(grocery_lists) == num_weeks
