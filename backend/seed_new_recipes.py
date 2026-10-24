#!/usr/bin/env python3
"""Seed-Skript: Importiert die 216 neuen Rezepte aus recipes_sammlung.json."""
import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.database import Ingredient, Recipe, RecipeIngredient, Household
from app.repositories.base import BaseRepository
from sqlalchemy import select

# Ersten Household (Demo) als owner verwenden
DEMO_HOUSEHOLD_ID = None


async def seed_new_recipes():
    global DEMO_HOUSEHOLD_ID
    print(f"\n{'='*50}")
    print(f"  Sprossa – Neue Rezepte importieren")
    print(f"  DB: {settings.database_url}")
    print(f"{'='*50}\n")

    async with async_session_factory() as session:
        ing_repo = BaseRepository(session, Ingredient)
        recipe_repo = BaseRepository(session, Recipe)

        # Bestehende Rezepte-Titel ermitteln (um Duplikate zu vermeiden)
        existing_titles = set()
        result = await session.execute(select(Recipe.title))
        for row in result:
            existing_titles.add(row[0].lower().strip())

        print(f"Bestehende Rezepte in DB: {len(existing_titles)}")

        # Ersten Household als Eigentümer
        hh_result = await session.execute(select(Household).limit(1))
        hh = hh_result.scalar_one_or_none()
        if hh:
            DEMO_HOUSEHOLD_ID = hh.id
        else:
            print("❌ Kein Household gefunden – bitte zuerst seed.py ausführen!")
            return

        # Bestehende Ingredient-Namen ermitteln (für Mapping)
        existing_ingredients = {}
        result = await session.execute(select(Ingredient))
        for row in result.scalars():
            existing_ingredients[row.name.lower()] = row

        print(f"Bestehende Zutaten in DB: {len(existing_ingredients)}")

        # Neue Rezepte laden
        seed_file = BACKEND_DIR.parent / "seed_data" / "recipes_sammlung.json"
        with open(seed_file) as f:
            new_recipes = json.load(f)

        imported = 0
        skipped = 0
        ingredients_created = 0

        for recipe_data in new_recipes:
            title = recipe_data["title"].strip()
            if title.lower() in existing_titles:
                skipped += 1
                continue

            # Rezept anlegen
            recipe = Recipe(
                household_id=DEMO_HOUSEHOLD_ID,
                title=title,
                description=recipe_data.get("description", ""),
                servings=recipe_data.get("servings", 4),
                prep_time_minutes=recipe_data.get("prep_time_minutes"),
                cook_time_minutes=recipe_data.get("cook_time_minutes"),
                difficulty=recipe_data.get("difficulty", "easy"),
                instructions=recipe_data.get("instructions", ""),
                source=recipe_data.get("source", "Webrecherche"),
                kid_friendly_tip=recipe_data.get("kid_friendly_tip"),
                cook_once_eat_twice=recipe_data.get("cook_once_eat_twice", False),
                tags=recipe_data.get("tags", []),
                is_public=True,
            )
            session.add(recipe)
            await session.flush()

            # Zutaten verknüpfen
            for ing_data in recipe_data.get("ingredients", []):
                ing_name = ing_data["name"].strip().lower()
                if ing_name not in existing_ingredients:
                    # Neue Zutat anlegen
                    ing = Ingredient(
                        name=ing_data["name"].strip(),
                        category=ing_data.get("category", "other"),
                        unit_default=ing_data.get("unit", "g"),
                    )
                    session.add(ing)
                    await session.flush()
                    existing_ingredients[ing_name] = ing
                    ingredients_created += 1

                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=existing_ingredients[ing_name].id,
                    quantity=ing_data.get("quantity", 1),
                    unit=ing_data.get("unit", "g"),
                )
                session.add(ri)

            existing_titles.add(title.lower())
            imported += 1

        await session.commit()
        print(f"\n✅ Import abgeschlossen!")
        print(f"   Neu importiert: {imported} Rezepte")
        print(f"   Übersprungen (Duplikate): {skipped}")
        print(f"   Neue Zutaten angelegt: {ingredients_created}")
        print(f"   Gesamt Rezepte in DB: {len(existing_titles)}")

        # Winter-/Herbst-Rezepte zählen
        all_recipes = await session.execute(select(Recipe))
        winter_count = 0
        autumn_count = 0
        for r in all_recipes.scalars():
            tags = [t.lower() for t in (r.tags or [])]
            title_lower = r.title.lower()
            if 'winter' in tags:
                winter_count += 1
            # Herbst: Kürbis, Pilze, Apfel, etc.
            autumn_keywords = ['kürbis', 'kastanie', 'maroni', 'federkohl', 'pastinake']
            if any(kw in title_lower for kw in autumn_keywords):
                autumn_count += 1

        print(f"\n🍂 Herbst-Rezepte (Kürbis/Kastanie etc.): {autumn_count}")
        print(f"❄️ Winter-Rezepte (mit winter-Tag): {winter_count}")


if __name__ == "__main__":
    asyncio.run(seed_new_recipes())