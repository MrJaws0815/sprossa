"""Grocery-Engine: Aus Wochen-/Monatsplänen Einkaufslisten generieren.

Domain-Regeln (TDD-Anker):
1. Alle Zutaten über alle Slots eines Zeitraums werden summiert
2. CookOnce-EatTwice-Rezepte werden NUR einfach in die Summe eingerechnet
3. Zutaten werden nach Kategorie gruppiert (Gemüse, Fleisch, etc.)
4. Selbe Zutat (gleiche Einheit) wird aufsummiert
5. Optionale Zutaten werden gesondert markiert
6. Substitutionen werden angewandt falls konfiguriert
"""
from collections import defaultdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    GroceryItem as GroceryItemModel,
    GroceryList as GroceryListModel,
    MealSlot,
    Recipe,
    RecipeIngredient,
    WeeklyPlan,
)
from app.repositories.grocery import GroceryItemRepository, GroceryListRepository
from app.repositories.ingredient import IngredientRepository
from app.repositories.recipe import RecipeRepository


# ─── Legacy: In-Memory Dummy-Cache für bestehende Tests ──────────────────

_RECIPE_CACHE: dict[UUID, list[dict]] = {}

def register_dummy_recipe(recipe_id: UUID, ingredients: list[dict]):
    """Registriert ein Rezept mit Zutaten für Tests/Prototypen."""
    _RECIPE_CACHE[recipe_id] = ingredients

def _get_recipe_ingredients(recipe_id: UUID) -> list[dict]:
    """Holt Zutaten für ein Rezept (Dummy-Cache)."""
    return _RECIPE_CACHE.get(recipe_id, [])


def build_grocery_list(
    weekly_plan: dict,
    ingredients_lookup: dict[UUID, dict],
    apply_substitutions: Optional[dict[str, str]] = None,
) -> dict:
    """Erzeugt eine Einkaufsliste aus einem Wochenplan (Legacy, In-Memory).

    weekly_plan: {
        "meal_slots": [ { "recipe_id": UUID, "meal_type": str, "servings_multiplier": float, "is_repeat": bool }, ... ]
    }
    ingredients_lookup: { ingredient_id: { "name": str, "category": str } }

    Rückgabe: {
        "items": [ { "ingredient_id": UUID, "name": str, "category": str, "total_quantity": float, "unit": str }, ... ],
        "grouped": { "vegetables": [...], "meat": [...], ... }
    }
    """
    aggregated: dict[UUID, GroceryItemBuilder] = {}

    for slot in weekly_plan.get("meal_slots", []):
        if slot.get("is_repeat", False):
            continue  # CookOnce-EatTwice: nur einmal einkaufen

        recipe_id = slot["recipe_id"]
        servings_mult = slot.get("servings_multiplier", 1.0)

        recipe_ingredients = _get_recipe_ingredients(recipe_id)

        for ri in recipe_ingredients:
            iid = ri["ingredient_id"]
            if iid not in aggregated:
                info = ingredients_lookup.get(iid, {"name": "?", "category": "other"})
                aggregated[iid] = GroceryItemBuilder(iid, info["name"], info["category"])

            qty = ri["quantity"] * servings_mult
            aggregated[iid].add(qty, ri["unit"], ri.get("substitution_note"))

    # Gruppieren
    grouped: dict[str, list] = defaultdict(list)
    items = []
    for builder in aggregated.values():
        item = {
            "ingredient_id": str(builder.ingredient_id),
            "name": builder.name,
            "category": builder.category,
            "total_quantity": round(builder.total_quantity, 2),
            "unit": builder.unit,
            "notes": builder.notes,
        }
        items.append(item)
        grouped[builder.category].append(item)

    return {"items": items, "grouped": dict(grouped)}


class GroceryItemBuilder:
    """Baut einen Einkaufslisten-Posten aus einer Zutat + Menge."""
    def __init__(self, ingredient_id: UUID, name: str, category: str):
        self.ingredient_id = ingredient_id
        self.name = name
        self.category = category
        self.total_quantity = 0.0
        self.unit = ""
        self.notes: list[str] = []

    def add(self, quantity: float, unit: str, note: Optional[str] = None):
        """Addiert eine Menge; prüft Einheiten-Konsistenz."""
        if self.unit and self.unit != unit:
            # TODO: Einheiten-Konvertierung (g -> kg, ml -> l)
            self.notes.append(f"+{quantity}{unit} (andere Einheit)")
        self.unit = unit if not self.unit else self.unit
        self.total_quantity += quantity
        if note:
            self.notes.append(note)


async def generate_and_persist_grocery_list(
    weekly_plan: WeeklyPlan,
    db: AsyncSession,
    household_id: UUID,
    monthly_plan_id: Optional[UUID] = None,
    week_number: Optional[int] = None,
) -> GroceryListModel:
    """Generiert eine Einkaufsliste aus einem WeeklyPlan und persistiert sie.

    Lädt Rezept-Zutaten aus der DB, aggregiert sie (CookOnce-Respekt),
    und schreibt GroceryList + GroceryItems in die Datenbank.
    """
    # Lade alle Recipe-IDs aus den MealSlots
    meal_slots = weekly_plan.meal_slots
    recipe_ids = list({s.recipe_id for s in meal_slots})

    # Rezepte mit Zutaten laden
    recipe_repo = RecipeRepository(db)
    recipes_with_ingredients = {}
    for rid in recipe_ids:
        recipe = await recipe_repo.get_with_ingredients(rid)
        if recipe:
            recipes_with_ingredients[rid] = recipe

    # Ingredient-Lookup (Name, Kategorie)
    ing_repo = IngredientRepository(db)
    all_ingredients = await ing_repo.get_all()
    ingredient_lookup = {i.id: {"name": i.name, "category": i.category} for i in all_ingredients}

    # Aggregieren
    aggregated: dict[UUID, GroceryItemBuilder] = {}

    for slot in meal_slots:
        if slot.is_repeat:
            continue  # CookOnce-EatTwice: nur einmal einkaufen

        recipe = recipes_with_ingredients.get(slot.recipe_id)
        if not recipe:
            continue

        servings_mult = slot.servings_multiplier

        for ri in recipe.ingredients:
            iid = ri.ingredient_id
            if iid not in aggregated:
                info = ingredient_lookup.get(iid, {"name": "?", "category": "other"})
                aggregated[iid] = GroceryItemBuilder(iid, info["name"], info["category"])

            qty = ri.quantity * servings_mult
            aggregated[iid].add(qty, ri.unit, ri.substitution_note)

    # GroceryList anlegen
    gl_repo = GroceryListRepository(db)
    grocery_list = await gl_repo.create(
        household_id=household_id,
        monthly_plan_id=monthly_plan_id,
        week_number=week_number,
        is_master_list=(week_number is None),
    )

    # GroceryItems anlegen
    gi_repo = GroceryItemRepository(db)
    for builder in aggregated.values():
        await gi_repo.create(
            grocery_list_id=grocery_list.id,
            ingredient_id=builder.ingredient_id,
            quantity_total=round(builder.total_quantity, 2),
            unit=builder.unit,
            category_override=builder.category,
            notes="; ".join(builder.notes) if builder.notes else None,
        )

    await db.refresh(grocery_list)
    return grocery_list