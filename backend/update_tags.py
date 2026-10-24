#!/usr/bin/env python3
"""Updatet Tags aller Rezepte in der DB (ohne Daten zu löschen)."""
import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import async_session_factory
from app.models.database import Recipe
from sqlalchemy import select


async def update_tags():
    print(f"{'='*50}")
    print(f"  Sprossa – Rezept-Tags aktualisieren")
    print(f"{'='*50}\n")

    async with async_session_factory() as session:
        # Alle aktuellen Rezepte aus DB laden
        result = await session.execute(select(Recipe))
        db_recipes = {r.title.lower(): r for r in result.scalars()}

        print(f"Rezepte in DB: {len(db_recipes)}")

        # Seed-Dateien laden (mit aktualisierten Tags)
        seed_dir = BACKEND_DIR.parent / "seed_data"
        
        updated = 0
        not_found = []

        for seed_file in ["recipes.json", "recipes_sammlung.json"]:
            with open(seed_dir / seed_file) as f:
                seed_recipes = json.load(f)

            for sr in seed_recipes:
                title = sr["title"].strip()
                key = title.lower()
                if key in db_recipes:
                    recipe = db_recipes[key]
                    old_tags = recipe.tags or []
                    new_tags = sr.get("tags", [])
                    if set(old_tags) != set(new_tags):
                        recipe.tags = new_tags
                        updated += 1
                else:
                    not_found.append(title)

        await session.commit()
        print(f"\n✅ Tags aktualisiert: {updated} Rezepte")
        if not_found:
            print(f"⚠️  Nicht in DB gefunden: {len(not_found)}")
            for t in not_found[:5]:
                print(f"    - {t}")

        # Zusammenfassung
        result = await session.execute(select(Recipe))
        all_recipes = list(result.scalars())
        
        for allergen in ['gluten', 'laktose', 'nuesse', 'ei', 'soja']:
            count = sum(1 for r in all_recipes if allergen in [t.lower() for t in (r.tags or [])])
            print(f"  {allergen}: {count} Rezepte")

        print(f"\nGesamt Rezepte in DB: {len(all_recipes)}")


if __name__ == "__main__":
    asyncio.run(update_tags())