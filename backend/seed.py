#!/usr/bin/env python3
"""Seed-Skript: Lädt Rezepte + Zutaten aus seed_data/ und erstellt Demo-User.

Lauffähig mit:
    cd backend && python3 seed.py

Löscht bei jedem Lauf alte Daten und legt alle neu an (sauberer Re-Import).
"""
import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
SEED_DIR = BACKEND_DIR.parent / "seed_data"

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.auth import hash_password
from app.models.database import Ingredient, Recipe, RecipeIngredient, User, Household, Member
from app.repositories.base import BaseRepository
from sqlalchemy import select, text


async def seed():
    print(f"\n{'='*50}")
    print(f"  Sprossa – Seed-Skript")
    print(f"  DB: {settings.database_url}")
    print(f"{'='*50}\n")

    async with async_session_factory() as session:
        ing_repo = BaseRepository(session, Ingredient)
        recipe_repo = BaseRepository(session, Recipe)
        user_repo = BaseRepository(session, User)
        hh_repo = BaseRepository(session, Household)
        member_repo = BaseRepository(session, Member)

        # ── Vorab: Alte Daten löschen (sauberer Re-Import) ────
        print("🗑  Alte Daten löschen...")
        await session.execute(text("DELETE FROM recipe_ingredients"))
        await session.execute(text("DELETE FROM recipes"))
        await session.execute(text("DELETE FROM ingredients"))
        await session.execute(text("DELETE FROM members"))
        await session.execute(text("DELETE FROM households"))
        await session.execute(text("DELETE FROM users"))
        print("  ✓ Alte Daten gelöscht\n")

        # ── 1. Zutaten importieren ─────────────────────────────
        print("📦 1. Zutaten importieren")
        ingredients_path = SEED_DIR / "ingredients.json"
        if not ingredients_path.exists():
            print(f"  ❌ Datei nicht gefunden: {ingredients_path}")
            return

        with open(ingredients_path) as f:
            ingredients_data = json.load(f)

        new_ingredients = []
        for item in ingredients_data:
            ing = Ingredient(
                name=item["name"],
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
        print(f"  ✓ {len(new_ingredients)} Zutaten neu angelegt\n")

        # ── 2. Alle Zutaten als Dict ───────────────────────────
        all_ingredients: dict[str, Ingredient] = {}
        stmt = select(Ingredient)
        result = await session.execute(stmt)
        for ing in result.scalars().all():
            all_ingredients[ing.name] = ing

        # ── 3. Rezepte importieren ─────────────────────────────
        print("🍽 2. Rezepte importieren")
        recipes_path = SEED_DIR / "recipes.json"
        if not recipes_path.exists():
            print(f"  ❌ Datei nicht gefunden: {recipes_path}")
            return

        with open(recipes_path) as f:
            recipes_data = json.load(f)

        print(f"  → {len(recipes_data)} Rezepte in Datei gefunden")
        pending_recipes = list(recipes_data)
        print(f"  ✓ {len(pending_recipes)} Rezepte neu anzulegen\n")

        # ── 4. Demo-User + Household + Members ─────────────────
        print("👤 3. Demo-User anlegen")
        demo_email = "demo@sprossa.de"
        demo_user = User(
            email=demo_email,
            password_hash=hash_password("demo1234"),
            display_name="Demo Familie",
        )
        session.add(demo_user)
        await session.flush()
        await session.refresh(demo_user)
        print(f"  ✓ User: {demo_user.email} (id={demo_user.id})\n")

        # Household
        print("🏠 4. Household + Members anlegen")
        household = Household(name="Familie Sprossa", user_id=demo_user.id)
        session.add(household)
        await session.flush()
        await session.refresh(household)
        print(f"  ✓ Household: {household.name} (id={household.id})")

        # Members
        member_specs = [
            {"name": "Mama", "age": 35},
            {"name": "Papa", "age": 38},
            {"name": "Kind 1", "age": 8},
            {"name": "Kind 2", "age": 5},
        ]
        for spec in member_specs:
            member = Member(
                household_id=household.id,
                name=spec["name"],
                age=spec["age"],
            )
            session.add(member)
        await session.flush()
        print(f"  ✓ {len(member_specs)} Members neu angelegt\n")

        # ── 5. Rezepte mit household_id befüllen ───────────────
        if pending_recipes:
            print(f"🍽 5. Rezepte in Household schreiben")
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
                for ing_ref in item.get("ingredient_list", item.get("ingredients", [])):
                    ing_name = ing_ref["name"]
                    ingredient = all_ingredients.get(ing_name)
                    if ingredient is None:
                        print(f"  ⚠ Zutat '{ing_name}' nicht gefunden – Rezept '{item['title']}' überspringe sie")
                        continue
                    ri = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=ing_ref.get("amount", ing_ref.get("quantity", 0)),
                        unit=ing_ref.get("unit", "Stück"),
                    )
                    session.add(ri)

            await session.flush()
            print(f"  ✓ {len(pending_recipes)} Rezepte mit Zutaten verknüpft\n")

        # ── Commit ─────────────────────────────────────────────
        await session.commit()

    print(f"{'='*50}")
    print(f"  ✅ Seed abgeschlossen!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(seed())