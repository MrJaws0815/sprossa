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


def build_grocery_list(
    weekly_plan: dict,
    ingredients_lookup: dict[UUID, dict],
    apply_substitutions: Optional[dict[str, str]] = None,
) -> dict:
    """Erzeugt eine Einkaufsliste aus einem Wochenplan.
    
    weekly_plan: {
        "meal_slots": [ { "recipe_id": UUID, "meal_type": str, "servings_multiplier": float, "is_repeat": bool }, ... ]
    }
    ingredients_lookup: { ingredient_id: { "name": str, "category": str } }
    
    Rückgabe: {
        "items": [ { "ingredient_id": UUID, "name": str, "category": str, "total_quantity": float, "unit": str }, ... ],
        "grouped": { "vegetables": [...], "meat": [...], ... }
    }
    """
    # Hier müssten wir die Rezepte laden und deren Zutaten abrufen
    # Für den ersten TDD-Ansatz arbeiten wir mit einer vereinfachten Struktur
    # Die echte Implementierung kommt später mit DB-Anbindung
    
    aggregated: dict[UUID, GroceryItemBuilder] = {}
    
    for slot in weekly_plan.get("meal_slots", []):
        if slot.get("is_repeat", False):
            continue  # CookOnce-EatTwice: nur einmal einkaufen
        
        recipe_id = slot["recipe_id"]
        servings_mult = slot.get("servings_multiplier", 1.0)
        
        # TODO: Rezept-Zutaten aus DB laden
        # Für den Moment: Dummy-Zutaten aus ingredients_lookup
        # Diese werden via Callback geliefert
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


# ─── Dummy-Resolver (wird später durch DB-Repository ersetzt) ────────────

_RECIPE_CACHE: dict[UUID, list[dict]] = {}

def register_dummy_recipe(recipe_id: UUID, ingredients: list[dict]):
    """Registriert ein Rezept mit Zutaten für Tests/Prototypen."""
    _RECIPE_CACHE[recipe_id] = ingredients

def _get_recipe_ingredients(recipe_id: UUID) -> list[dict]:
    """Holt Zutaten für ein Rezept (erst Dummy-Cache, später DB)."""
    return _RECIPE_CACHE.get(recipe_id, [])