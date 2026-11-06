"""Exception-Case-Matrix für Task 35 / Launch-Kriterium H4.

Deckt die Fälle ab, die im Launch-Kriterium „Exception Cases vollständig"
genannt sind:

    Allergien · Abneigungen · Kinderalter · Haushaltsgröße 1–8 ·
    fehlende Zutaten

Grundsätze:
- Produktcode wird hier NICHT angepasst; die Tests beschreiben das
  dokumentierte Soll-Verhalten (klarer HTTP 400 statt stillem Fallback,
  weiche Regel bei Abneigungen, kein Crash bei Datenlücken).
- DB-Tests laufen gegen die Test-DB (localhost:5433/sprossa_test) und legen
  ausschließlich eigene Fixture-Zeilen an. Der Cleanup löscht nur Haushalte,
  die dieses Modul selbst erzeugt hat (`household_id`-Skopus), niemals
  Seed- oder Fremddaten.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text

from app.core.auth import hash_password
from app.core.database import async_session_factory
from app.models.database import (
    GroceryItem,
    GroceryList,
    Household,
    Ingredient,
    MealSlot,
    Recipe,
    RecipeIngredient,
    User,
    WeeklyPlan,
)
from app.services.plan_generator import (
    GeneratorConfig,
    calculate_total_portions,
    generate_and_persist_monthly_plan,
)

MONTH = 11
YEAR = 2026


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def db():
    """Async-Session gegen die Test-DB; Rollback am Ende."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def catalog(db):
    """Fabrik für isolierte Test-Kataloge.

    `catalog(recipes=3, ingredients=[("Karotten", "vegetables")], tags=[...])`
    legt User + Household + Zutaten + Rezepte an und gibt sie zurück.
    Alle erzeugten Zeilen werden nach dem Test wieder entfernt.
    """
    created = {"households": [], "users": [], "ingredients": []}

    async def _make(
        recipes: int = 6,
        ingredients: list[tuple[str, str]] | None = None,
        tags: list[str] | None = None,
        title_prefix: str = "Fixturegericht",
        with_recipe_ingredients: bool = True,
    ) -> dict:
        suffix = uuid.uuid4().hex[:8]
        user = User(
            email=f"exc-{suffix}@e2e.de",
            password_hash=hash_password("test1234"),
            display_name="Exception-Test",
        )
        db.add(user)
        await db.flush()
        household = Household(name=f"Exc-Haushalt-{suffix}", user_id=user.id)
        db.add(household)
        await db.flush()
        created["users"].append(user.id)
        created["households"].append(household.id)

        specs = ingredients if ingredients is not None else [
            ("Karotten", "vegetables"),
            ("Hähnchenbrust", "meat"),
        ]
        ings = []
        for name, category in specs:
            ing = Ingredient(
                name=f"{name}_{suffix}", category=category, unit_default="g"
            )
            db.add(ing)
            ings.append(ing)
        await db.flush()
        created["ingredients"].extend(i.id for i in ings)

        created_recipes = []
        for i in range(recipes):
            recipe = Recipe(
                household_id=household.id,
                title=f"{title_prefix} {i + 1} {suffix}",
                servings=4,
                cook_once_eat_twice=(i < 2),
                tags=tags if tags is not None else ["schnell"],
            )
            db.add(recipe)
            await db.flush()
            if with_recipe_ingredients:
                for ing in ings:
                    db.add(
                        RecipeIngredient(
                            recipe_id=recipe.id,
                            ingredient_id=ing.id,
                            quantity=200.0,
                            unit="g",
                        )
                    )
            created_recipes.append(recipe)
        await db.flush()

        return {
            "user": user,
            "household": household,
            "recipes": created_recipes,
            "ingredients": ings,
        }

    yield _make

    # Cleanup: ausschließlich selbst erzeugte Zeilen, kind-first (FK-Reihenfolge).
    hids = created["households"]
    if hids:
        statements = [
            "DELETE FROM grocery_items WHERE grocery_list_id IN "
            "(SELECT id FROM grocery_lists WHERE household_id = ANY(:h))",
            "DELETE FROM grocery_lists WHERE household_id = ANY(:h)",
            "DELETE FROM meal_slots WHERE weekly_plan_id IN "
            "(SELECT id FROM weekly_plans WHERE household_id = ANY(:h))",
            "DELETE FROM weekly_plans WHERE household_id = ANY(:h)",
            "DELETE FROM monthly_plans WHERE household_id = ANY(:h)",
            "DELETE FROM recipe_ingredients WHERE recipe_id IN "
            "(SELECT id FROM recipes WHERE household_id = ANY(:h))",
            "DELETE FROM recipes WHERE household_id = ANY(:h)",
            "DELETE FROM members WHERE household_id = ANY(:h)",
            "DELETE FROM households WHERE id = ANY(:h)",
        ]
        for stmt in statements:
            await db.execute(text(stmt), {"h": hids})
    if created["ingredients"]:
        await db.execute(
            text("DELETE FROM ingredients WHERE id = ANY(:i)"),
            {"i": created["ingredients"]},
        )
    if created["users"]:
        await db.execute(
            text("DELETE FROM users WHERE id = ANY(:u)"), {"u": created["users"]}
        )
    await db.commit()


def _config(data: dict, **overrides) -> GeneratorConfig:
    kwargs = dict(
        household_id=data["household"].id,
        month=MONTH,
        year=YEAR,
        member_ids=[],
        recipe_ids=[r.id for r in data["recipes"]],
    )
    kwargs.update(overrides)
    return GeneratorConfig(**kwargs)


async def _count_grocery_items(db, monthly_plan_id) -> tuple[int, int]:
    lists = (
        await db.execute(
            select(GroceryList).where(GroceryList.monthly_plan_id == monthly_plan_id)
        )
    ).scalars().all()
    items = 0
    for grocery_list in lists:
        items += len(
            (
                await db.execute(
                    select(GroceryItem).where(
                        GroceryItem.grocery_list_id == grocery_list.id
                    )
                )
            ).scalars().all()
        )
    return len(lists), items


# ─────────────────────────────────────────────────────────────────────────
# Kinderalter & Haushaltsgröße (reine Rechenlogik, ohne DB)
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "age,expected",
    [
        (None, 1.0),   # Alter unbekannt → Erwachsenen-Faktor
        (0, 0.3),      # Säugling
        (3, 0.3),
        (4, 0.5),      # Kleinkind-Grenze
        (7, 0.5),
        (8, 0.7),      # Grundschul-Grenze
        (12, 0.7),
        (13, 1.0),     # Teenager-Grenze
        (99, 1.0),
    ],
)
def test_kinderalter_grenzwerte(age, expected):
    """Altersgrenzen 0/3/4/7/8/12/13 dürfen nicht verrutschen."""
    members = [{"age": age}] if age is not None else [{"age": None}]
    assert calculate_total_portions(members) == pytest.approx(expected)


def test_haushaltsgroesse_1_person():
    assert calculate_total_portions([{"age": 35}]) == pytest.approx(1.0)


def test_haushaltsgroesse_8_personen():
    """2 Erwachsene + 6 Kinder (12/10/8/6/4/2) → 5.4 Portionen."""
    members = [
        {"age": 40}, {"age": 38}, {"age": 12}, {"age": 10},
        {"age": 8}, {"age": 6}, {"age": 4}, {"age": 2},
    ]
    assert calculate_total_portions(members) == pytest.approx(5.4)


def test_portion_factor_aus_profil_schlaegt_alter():
    """Gespeicherter Faktor (dietary_goals.portion_factor) hat Vorrang."""
    members = [{"age": 40, "dietary_goals": {"portion_factor": 1.5}}]
    assert calculate_total_portions(members) == pytest.approx(1.5)


def test_negativer_portion_factor_wird_ignoriert():
    """Unsinnige Werte (< 0) fallen auf die Altersschätzung zurück."""
    members = [{"age": 40, "dietary_goals": {"portion_factor": -2}}]
    assert calculate_total_portions(members) == pytest.approx(1.0)


def test_leere_haushaltsliste_ergibt_null():
    """Kein Mitglied → 0.0 (kein Division-durch-Null-Fehler)."""
    assert calculate_total_portions([]) == 0.0


# ─────────────────────────────────────────────────────────────────────────
# Allergien
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_allergie_ohne_treffer_ergibt_400(db, catalog):
    """Nuss-Allergie bei ausschließlich nusshaltigem Katalog → 400."""
    data = await catalog(
        recipes=3, ingredients=[("Walnüsse", "nuts")], tags=["schnell"]
    )
    config = _config(data, members=[{"age": 30, "allergies": ["nüsse"]}])

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400
    assert "Allergene" in exc.value.detail


@pytest.mark.asyncio
async def test_allergie_ascii_schreibweise_wird_normalisiert(db, catalog):
    """'nuesse' (ASCII) muss genauso filtern wie 'nüsse' (Umlaut)."""
    data = await catalog(
        recipes=3, ingredients=[("Walnüsse", "nuts")], tags=["schnell"]
    )
    config = _config(data, members=[{"age": 30, "allergies": ["nuesse"]}])

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_haushalts_allergie_als_string_ergibt_400(db, catalog):
    """Allergie als String statt Liste (Frontend-Altdaten) darf nicht crashen."""
    data = await catalog(
        recipes=3, ingredients=[("Walnüsse", "nuts")], tags=["schnell"]
    )
    config = _config(
        data,
        dietary_profile={"allergies": "nüsse"},
    )

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_allergiker_mit_ausweichrezepten_bekommt_plan(db, catalog):
    """Gemischt: Rezepte mit/ohne Allergen → Plan entsteht, Allergen fliegt raus."""
    data = await catalog(
        recipes=6,
        ingredients=[("Karotten", "vegetables")],
        tags=["schnell"],
    )
    # 3 Rezepte zusätzlich mit Walnüssen anreichern
    nut = Ingredient(
        name=f"Walnüsse_{uuid.uuid4().hex[:6]}", category="nuts", unit_default="g"
    )
    db.add(nut)
    await db.flush()
    try:
        for recipe in data["recipes"][:3]:
            db.add(
                RecipeIngredient(
                    recipe_id=recipe.id, ingredient_id=nut.id, quantity=50.0, unit="g"
                )
            )
        await db.flush()

        config = _config(data, members=[{"age": 30, "allergies": ["nüsse"]}])
        monthly = await generate_and_persist_monthly_plan(config, db)

        slots = (
            await db.execute(
                select(MealSlot)
                .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
                .where(WeeklyPlan.monthly_plan_id == monthly.id)
            )
        ).scalars().all()
        assert slots, "Plan muss Mahlzeiten enthalten"
        used = {slot.recipe_id for slot in slots}
        assert used <= {r.id for r in data["recipes"][3:]}, (
            "Rezepte mit Walnüssen dürfen bei Nuss-Allergie nicht im Plan landen"
        )
    finally:
        # Aufräumen der zusätzlichen Zutat (nicht Teil der catalog-Fixture)
        await db.execute(
            text("DELETE FROM recipe_ingredients WHERE ingredient_id = :i"),
            {"i": nut.id},
        )
        await db.execute(text("DELETE FROM ingredients WHERE id = :i"), {"i": nut.id})


# ─────────────────────────────────────────────────────────────────────────
# Ernährungsprofil
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vegan_ohne_treffer_ergibt_400(db, catalog):
    """Veganes Profil, aber nur Fleischrezepte → klarer 400, kein Fallback."""
    data = await catalog(
        recipes=3,
        ingredients=[("Karotten", "vegetables"), ("Hähnchenbrust", "meat")],
        tags=["fleisch", "schnell"],
    )
    config = _config(data, dietary_profile={"diet_types": ["vegan"]})

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400
    assert "Ernährungsprofil" in exc.value.detail


# ─────────────────────────────────────────────────────────────────────────
# Fokus-Tags & Saison
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fokustag_ohne_treffer_ergibt_400(db, catalog):
    data = await catalog(recipes=3, tags=["schnell"])
    config = _config(data, focus_tags=["gibt-es-nicht"])

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400
    assert "Fokustags" in exc.value.detail


@pytest.mark.asyncio
async def test_saison_ohne_treffer_ergibt_400(db, catalog):
    """Nur Sommer-Rezepte im November → 400 statt unpassendem Plan."""
    data = await catalog(recipes=3, tags=["sommer", "schnell"])
    config = _config(data)

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400
    assert "saisonal" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_nur_platzhalter_rezepte_ergibt_400(db, catalog):
    """Nur Demo-/Testrezepte im Katalog → 400, niemals Platzhalter im Plan."""
    data = await catalog(recipes=3, title_prefix="Testrezept")
    config = _config(data)

    with pytest.raises(HTTPException) as exc:
        await generate_and_persist_monthly_plan(config, db)
    assert exc.value.status_code == 400


# ─────────────────────────────────────────────────────────────────────────
# Abneigungen (weiche Regel)
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_abneigung_blockiert_plan_nicht(db, catalog):
    """Kleiner Katalog + Abneigung gegen Hauptzutat → Plan entsteht trotzdem."""
    data = await catalog(recipes=6, ingredients=[("Karotten", "vegetables")])
    config = _config(
        data, dietary_profile={"disliked_ingredients": ["Karotten"]}
    )

    monthly = await generate_and_persist_monthly_plan(config, db)

    slots = (
        await db.execute(
            select(MealSlot)
            .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
        )
    ).scalars().all()
    assert slots, "Abneigung darf die Planerstellung nicht verhindern"


@pytest.mark.asyncio
async def test_abneigung_als_string_wird_geparst(db, catalog):
    """'Karotten, Pilze' als String (Altdaten) darf nicht crashen."""
    data = await catalog(recipes=6, ingredients=[("Karotten", "vegetables")])
    config = _config(
        data, dietary_profile={"dislikes": "Karotten, Pilze"}
    )

    monthly = await generate_and_persist_monthly_plan(config, db)
    assert monthly.id is not None


# ─────────────────────────────────────────────────────────────────────────
# Haushaltsgröße 1 und 8 (DB-Durchlauf mit Portionsskalierung)
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_haushalt_1_person_skaliert_portionen(db, catalog):
    """1 Person bei Rezeptbasis 4 → Multiplier 0.25."""
    data = await catalog(recipes=6)
    config = _config(data, members=[{"age": 35}], total_portions=1.0)

    monthly = await generate_and_persist_monthly_plan(config, db)
    slots = (
        await db.execute(
            select(MealSlot)
            .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    assert slots
    multipliers = {round(s.servings_multiplier, 3) for s in slots if s.servings_multiplier}
    assert multipliers == {0.25}


@pytest.mark.asyncio
async def test_haushalt_8_personen_skaliert_portionen(db, catalog):
    """8 Personen (5.4 Portionen) bei Rezeptbasis 4 → Multiplier 1.35."""
    data = await catalog(recipes=6)
    members = [
        {"age": 40}, {"age": 38}, {"age": 12}, {"age": 10},
        {"age": 8}, {"age": 6}, {"age": 4}, {"age": 2},
    ]
    total = calculate_total_portions(members)
    config = _config(data, members=members, total_portions=total)

    monthly = await generate_and_persist_monthly_plan(config, db)
    slots = (
        await db.execute(
            select(MealSlot)
            .join(WeeklyPlan, MealSlot.weekly_plan_id == WeeklyPlan.id)
            .where(WeeklyPlan.monthly_plan_id == monthly.id)
        )
    ).scalars().all()

    assert slots
    multipliers = {round(s.servings_multiplier, 2) for s in slots if s.servings_multiplier}
    assert multipliers == {round(total / 4, 2)}


# ─────────────────────────────────────────────────────────────────────────
# Fehlende Zutaten
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rezepte_ohne_zutaten_erzeugen_leere_einkaufsliste(db, catalog):
    """Rezepte ganz ohne Zutaten: Plan + Liste entstehen, 0 Items, kein Crash."""
    data = await catalog(recipes=6, with_recipe_ingredients=False)
    config = _config(data, total_portions=4.0)

    monthly = await generate_and_persist_monthly_plan(config, db)
    n_lists, n_items = await _count_grocery_items(db, monthly.id)

    assert n_lists >= 1, "Einkaufsliste muss existieren, auch wenn sie leer ist"
    assert n_items == 0


@pytest.mark.asyncio
async def test_gemischte_rezepte_mit_und_ohne_zutaten(db, catalog):
    """Datensatzlücke: einige Rezepte ohne Zutaten → Plan ok, Items > 0."""
    data = await catalog(recipes=3, ingredients=[("Karotten", "vegetables")])
    suffix = uuid.uuid4().hex[:6]
    for i in range(3):
        recipe = Recipe(
            household_id=data["household"].id,
            title=f"OhneZutaten {i} {suffix}",
            servings=4,
            cook_once_eat_twice=False,
            tags=["schnell"],
        )
        db.add(recipe)
        data["recipes"].append(recipe)
    await db.flush()

    config = _config(data, total_portions=4.0)
    monthly = await generate_and_persist_monthly_plan(config, db)
    n_lists, n_items = await _count_grocery_items(db, monthly.id)

    assert n_lists >= 1
    assert n_items > 0, "Zutaten der vollständigen Rezepte müssen in der Liste landen"
