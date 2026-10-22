#!/usr/bin/env python
"""Seed recipe_ingredients links from recipes.json into the database.

Idempotent: deletes all existing recipe_ingredients before inserting.
Set MM_DATABASE_URL to override the target database.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# --- Point to test DB unless already overridden ---
os.environ.setdefault(
    "MM_DATABASE_URL",
    "postgresql+asyncpg://sprossa:sprossa@localhost:5433/sprossa_test",
)

# --- Project imports ---
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import async_session_factory
from app.models.database import RecipeIngredient
from sqlalchemy import delete, select


async def main() -> None:
    # 1. Load seed data
    seed_path = Path(__file__).resolve().parent / "seed_data" / "recipes.json"
    with open(seed_path) as f:
        recipes_data = json.load(f)

    async with async_session_factory() as session:
        # 2. Build lookup dicts from DB
        from app.models.database import Ingredient, Recipe

        result = await session.execute(select(Ingredient))
        ingredients_by_name: dict[str, int] = {
            row.name: row.id for row in result.scalars().all()
        }

        result = await session.execute(select(Recipe))
        recipes_by_title: dict[str, int] = {
            row.title: row.id for row in result.scalars().all()
        }

        # 3. Clear existing links
        await session.execute(delete(RecipeIngredient))
        await session.flush()

        # 4. Build new links
        created = 0
        skipped_recipe = 0
        skipped_ingredient = 0

        for recipe in recipes_data:
            title = recipe["title"]
            recipe_id = recipes_by_title.get(title)
            if recipe_id is None:
                print(f"  ⚠ SKIP recipe not in DB: {title!r}", file=sys.stderr)
                skipped_recipe += 1
                continue

            for ing in recipe.get("ingredient_list", []):
                name = ing["name"]
                ingredient_id = ingredients_by_name.get(name)
                if ingredient_id is None:
                    print(f"  ⚠ SKIP ingredient not in DB: {name!r} (recipe: {title!r})", file=sys.stderr)
                    skipped_ingredient += 1
                    continue

                link = RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=ingredient_id,
                    quantity=ing["amount"],
                    unit=ing["unit"],
                    is_optional=False,
                    pre_processed=False,
                )
                session.add(link)
                created += 1

        await session.commit()

    # 5. Report
    print(f"\n✅ Done — created {created} recipe_ingredient links")
    if skipped_recipe:
        print(f"   ⚠ {skipped_recipe} recipes not found in DB")
    if skipped_ingredient:
        print(f"   ⚠ {skipped_ingredient} ingredients not found in DB")


if __name__ == "__main__":
    asyncio.run(main())