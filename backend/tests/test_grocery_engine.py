"""Tests für die Grocery-Engine

TDD-Anker:
1. build_grocery_list() summierte Zutaten korrekt
2. CookOnce-Rezepte nur einmal in die Summe einrechnen
3. Gruppierung nach Kategorie funktioniert
4. Gleiche Zutaten werden aufsummiert
"""
import uuid

import pytest

from app.services.grocery_engine import build_grocery_list, register_dummy_recipe


# Beispiel-Zutaten
INGREDIENTS = {
    uuid.UUID("00000000-0000-0000-0000-000000000200"): {"name": "Karotten", "category": "vegetables"},
    uuid.UUID("00000000-0000-0000-0000-000000000201"): {"name": "Kartoffeln", "category": "vegetables"},
    uuid.UUID("00000000-0000-0000-0000-000000000202"): {"name": "Hähnchenbrust", "category": "meat"},
    uuid.UUID("00000000-0000-0000-0000-000000000203"): {"name": "Sahne", "category": "dairy"},
    uuid.UUID("00000000-0000-0000-0000-000000000204"): {"name": "Mehl", "category": "grains"},
    uuid.UUID("00000000-0000-0000-0000-000000000205"): {"name": "Butter", "category": "dairy"},
}

RID_A = uuid.UUID("00000000-0000-0000-0000-000000000100")
RID_B = uuid.UUID("00000000-0000-0000-0000-000000000101")


@pytest.fixture(autouse=True)
def setup_recipes():
    """Registriert Dummy-Rezepte für die Tests."""
    register_dummy_recipe(RID_A, [
        {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000200"), "quantity": 3.0, "unit": "Stück", "substitution_note": None},  # 3 Karotten
        {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000203"), "quantity": 200.0, "unit": "ml", "substitution_note": "Hafermilch"},  # Sahne
    ])
    register_dummy_recipe(RID_B, [
        {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000201"), "quantity": 500.0, "unit": "g", "substitution_note": None},  # 500g Kartoffeln
        {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000202"), "quantity": 2.0, "unit": "Stück", "substitution_note": None},  # 2 Hähnchenbrust
    ])


class TestGroceryListBuilding:
    """Grundlegende Einkaufslistenerstellung"""

    def test_ein_gericht_erzeugt_zutaten(self):
        """Ein Rezept erzeugt korrekte Einkaufsliste."""
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        assert len(result["items"]) == 2  # Karotten + Sahne

    def test_zwei_gerichte_summiert_mengen(self):
        """Zwei verschiedene Rezepte → Zutaten werden summiert/getrennt."""
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
                {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        items = {i["name"]: i for i in result["items"]}
        assert "Karotten" in items
        assert "Kartoffeln" in items
        assert "Hähnchenbrust" in items
        assert "Sahne" in items


class TestCookOnceHandling:
    """Regel 2: CookOnce-Rezepte nur einmal einrechnen"""

    def test_cook_once_repeat_wird_ignoriert(self):
        """Ein Repeat-Slot wird nicht in die Einkaufsliste eingerechnet."""
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": True},  # CookOnce-Repeat
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        # Sahne = 200ml (nur einmal, nicht 400ml)
        sahne = [i for i in result["items"] if i["name"] == "Sahne"][0]
        assert sahne["total_quantity"] == 200.0


class TestGrouping:
    """Regel 3: Gruppierung nach Kategorie"""

    def test_items_sind_nach_kategorie_gruppiert(self):
        """Result enthält grouped dict mit Kategorie-Schlüsseln."""
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
                {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        assert "vegetables" in result["grouped"]
        assert "meat" in result["grouped"]
        assert "dairy" in result["grouped"]


class TestQuantitySummation:
    """Regel 4: Gleiche Zutaten aus verschiedenen Rezepten werden summiert"""

    def test_gleiche_zutat_ueber_verschiedene_rezepte(self):
        """Karotten aus Rezept A und B (wenn B auch Karotten hätte) werden summiert."""
        # Rezept B bekommt zusätzlich Karotten
        register_dummy_recipe(RID_B, [
            {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000200"), "quantity": 2.0, "unit": "Stück", "substitution_note": None},
        ])
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
                {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        karotten = [i for i in result["items"] if i["name"] == "Karotten"][0]
        assert karotten["total_quantity"] == 5.0  # 3 + 2


class TestServingsMultiplier:
    """Portionsmultiplikator beeinflusst die Menge"""

    def test_servings_multiplier_verdoppelt_mengen(self):
        """1.5x Portionen → Mengen × 1.5."""
        plan = {
            "meal_slots": [
                {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.5, "is_repeat": False},
            ]
        }
        result = build_grocery_list(plan, INGREDIENTS)
        karotten = [i for i in result["items"] if i["name"] == "Karotten"][0]
        assert karotten["total_quantity"] == 4.5  # 3 * 1.5
        sahne = [i for i in result["items"] if i["name"] == "Sahne"][0]
        assert sahne["total_quantity"] == 300.0  # 200 * 1.5