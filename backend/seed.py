#!/usr/bin/env python3
"""Seed-Skript: Lädt Rezepte + Zutaten aus seed_data/ und erstellt Demo-User.

Lauffähig mit:
    cd backend && python3 seed.py

Idempotent – bei Wiederholung keine Duplikate.
"""
import asyncio
import json
import sys
from pathlib import Path

# ── Pfad: backend/ muss im sys.path sein ──────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
SEED_DIR = BACKEND_DIR.parent / "seed_data"

# ── App-Imports (nach sys.path) ───────────────────────────────────────────
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.auth import hash_password
from app.models.database import Ingredient, Recipe, RecipeIngredient, User, Household, Member
from app.repositories.base import BaseRepository
from sqlalchemy import select


# ── Logger ────────────────────────────────────────────────────────────────
def log(label: str, items: list, singular: str = "Eintrag"):
    n = len(items)
    if n == 0:
        print(f"  ✗ {label}: 0 {singular} (bereits vorhanden)")
    else:
        print(f"  ✓ {label}: {n} {singular}{'e' if n != 1 else ''} neu angelegt")


# ── Core ──────────────────────────────────────────────────────────────────

async def seed():
    print(f"\n{'='*50}")
    print(f"  Monatsmenü – Seed-Skript")
    print(f"  DB: {settings.database_url}")
    print(f"{'='*50}\n")

    async with async_session_factory() as session:
        ing_repo = BaseRepository(session, Ingredient)
        recipe_repo = BaseRepository(session, Recipe)
        user_repo = BaseRepository(session, User)
        hh_repo = BaseRepository(session, Household)
        member_repo = BaseRepository(session, Member)

        # ── 1. Zutaten ────────────────────────────────────────────────────
        print("📦 1. Zutaten importieren")
        ingredients_path = SEED_DIR / "ingredients.json"
        if not ingredients_path.exists():
            print(f"  ❌ Datei nicht gefunden: {ingredients_path}")
            return

        with open(ingredients_path) as f:
            ingredients_data = json.load(f)

        new_ingredients = []
        for item in ingredients_data:
            name = item["name"]
            existing = await ing_repo.get_by_field("name", name)
            if existing is not None:
                continue
            ing = Ingredient(
                name=name,
                category=item["category"],
                unit_default=item.get("unit_default", "Stück"),
                storage=item.get("storage"),
            )
            session.add(ing)
            new_ingredients.append(ing)

        if new_ingredients:
            await session.flush()
            for ing in new_ingredients:
                await session.refresh(ing)
        log("Zutaten", new_ingredients, "Zutat")

        # ── 2. Alle Zutaten (inkl. bestehende) für Recipe-Linking laden ────
        all_ingredients: dict[str, Ingredient] = {}
        stmt = __import__("sqlalchemy").select(Ingredient)
        result = await session.execute(stmt)
        for ing in result.scalars().all():
            all_ingredients[ing.name] = ing

        # ── 3. Rezepte ────────────────────────────────────────────────────
        print("\n🍽  2. Rezepte importieren")
        recipes_path = SEED_DIR / "recipes.json"
        if not recipes_path.exists():
            print(f"  ❌ Datei nicht gefunden: {recipes_path}")
            return

        with open(recipes_path) as f:
            recipes_data = json.load(f)

        # Rezepte ohne household_id – wir brauchen erst den Household.
        # Zwischenspeichern: Titel → Daten inkl. Ingredient-Refs
        pending_recipes = []
        for item in recipes_data:
            title = item["title"]
            existing = await recipe_repo.get_by_field("title", title)
            if existing is not None:
                continue
            pending_recipes.append(item)

        log("Rezepte", pending_recipes, "Rezept")

        # ── 4. Demo-User + Household + Members ────────────────────────────
        print("\n👤  3. Demo-User anlegen")
        demo_email = "demo@sprossa.de"
        demo_user = await user_repo.get_by_field("email", demo_email)
        if demo_user is None:
            demo_user = User(
                email=demo_email,
                password_hash=hash_password("demo1234"),
                display_name="Demo Familie",
            )
            session.add(demo_user)
            await session.flush()
            await session.refresh(demo_user)
            print(f"  ✓ User: {demo_user.email} (id={demo_user.id})")
        else:
            print(f"  ✓ User existiert bereits: {demo_user.email}")

        # Household
        print("\n🏠  4. Household + Members anlegen")
        hh_name = "Familie Sprossa"
        existing_hh = await hh_repo.get_by_field("name", hh_name)
        if existing_hh is None:
            household = Household(name=hh_name, user_id=demo_user.id)
            session.add(household)
            await session.flush()
            await session.refresh(household)
            print(f"  ✓ Household: {household.name} (id={household.id})")
        else:
            household = existing_hh
            print(f"  ✓ Household existiert bereits: {household.name}")

        # Members
        member_specs = [
            {"name": "Mama", "age": 35},
            {"name": "Papa", "age": 38},
            {"name": "Kind 1 (8)", "name_clean": "Kind 1", "age": 8},
            {"name": "Kind 2 (5)", "name_clean": "Kind 2", "age": 5},
        ]
        new_members = 0
        for spec in member_specs:
            mname = spec.get("name_clean", spec["name"])
            stmt = select(Member).where(
                Member.household_id == household.id,
                Member.name == mname,
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing is not None:
                print(f"  - Member '{mname}' existiert bereits")
                continue
            member = Member(
                household_id=household.id,
                name=mname,
                age=spec["age"],
            )
            session.add(member)
            new_members += 1
        if new_members:
            await session.flush()
        print(f"  ✓ Members: {new_members} neu angelegt")

        # ── 5. Rezepte mit household_id befüllen ──────────────────────────
        if pending_recipes:
            print(f"\n🍽  5. Rezepte in Household schreiben")
            for item in pending_recipes:
                recipe = Recipe(
                    household_id=household.id,
                    title=item["title"],
                    description=item.get("description"),
                    servings=item.get("servings", 4),
                    prep_time_minutes=item.get("prep_time_minutes"),
                    cook_time_minutes=item.get("cook_time_minutes"),
                    difficulty=item.get("difficulty", "easy"),
                    instructions=item.get("instructions"),
                    is_public=item.get("is_public", False),
                    kid_friendly_tip=item.get("kid_friendly_tip"),
                    cook_once_eat_twice=item.get("cook_once_eat_twice", False),
                    tags=item.get("tags", []),
                )
                session.add(recipe)
                await session.flush()
                await session.refresh(recipe)

                # RecipeIngredient verknüpfen
                for ing_ref in item.get("ingredients", []):
                    ing_name = ing_ref["name"]
                    ingredient = all_ingredients.get(ing_name)
                    if ingredient is None:
                        print(f"  ⚠ Zutat '{ing_name}' nicht gefunden – Rezept '{item['title']}' überspringe sie")
                        continue
                    ri = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=ing_ref["quantity"],
                        unit=ing_ref["unit"],
                    )
                    session.add(ri)

            await session.flush()
            print(f"  ✓ {len(pending_recipes)} Rezepte mit Zutaten verknüpft")

        # ── Commit ────────────────────────────────────────────────────────
        await session.commit()

    print(f"\n{'='*50}")
    print(f"  ✅ Seed abgeschlossen!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(seed())