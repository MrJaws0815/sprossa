#!/usr/bin/env python3
"""Einzeltests für Plan-Generator und Grocery-Engine (unittest).
Lauffähig ohne externe Pakete – benötigt nur Python 3.13+ Standardbibliothek.
"""
import sys
import os
import uuid
import unittest

# Projekt-Root ins Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.plan_generator import (
    GeneratorConfig,
    generate_monthly_plan,
    generate_weekly_plan_skeleton,
    weeks_in_month,
)
from app.services.grocery_engine import build_grocery_list, register_dummy_recipe, _RECIPE_CACHE


# ─── Konstanten ────────────────────────────────────────────────────────────

SAMPLE_RECIPE_IDS = [
    uuid.UUID("00000000-0000-0000-0000-000000000100"),
    uuid.UUID("00000000-0000-0000-0000-000000000101"),
    uuid.UUID("00000000-0000-0000-0000-000000000102"),
    uuid.UUID("00000000-0000-0000-0000-000000000103"),
    uuid.UUID("00000000-0000-0000-0000-000000000104"),
    uuid.UUID("00000000-0000-0000-0000-000000000105"),
]

INGREDIENTS = {
    uuid.UUID("00000000-0000-0000-0000-000000000200"): {"name": "Karotten",    "category": "vegetables"},
    uuid.UUID("00000000-0000-0000-0000-000000000201"): {"name": "Kartoffeln",  "category": "vegetables"},
    uuid.UUID("00000000-0000-0000-0000-000000000202"): {"name": "Hähnchenbrust", "category": "meat"},
    uuid.UUID("00000000-0000-0000-0000-000000000203"): {"name": "Sahne",       "category": "dairy"},
    uuid.UUID("00000000-0000-0000-0000-000000000204"): {"name": "Mehl",        "category": "grains"},
    uuid.UUID("00000000-0000-0000-0000-000000000205"): {"name": "Butter",      "category": "dairy"},
}
RID_A = SAMPLE_RECIPE_IDS[0]   # 0000…0100
RID_B = SAMPLE_RECIPE_IDS[1]   # 0000…0101

CID = uuid.UUID("00000000-0000-0000-0000-000000000200")  # Karotte
PID = uuid.UUID("00000000-0000-0000-0000-000000000201")  # Kartoffel
HID = uuid.UUID("00000000-0000-0000-0000-000000000202")  # Hähnchen
MID = uuid.UUID("00000000-0000-0000-0000-000000000203")  # Sahne


# ─── Plan-Generator Tests ──────────────────────────────────────────────────

class TestWeeksInMonth(unittest.TestCase):
    """Regel 1: Monats-Wochenanzahl"""

    def test_januar_2025_hat_5_wochen(self):
        """Jan 2025 (31d, startet Mi) → 5 Planungswochen"""
        self.assertEqual(weeks_in_month(1, 2025), 5)

    def test_februar_2025_hat_4_wochen(self):
        """Feb 2025 (28d, startet Sa) → 4 (erste Woche nur 1 Tag)"""
        self.assertEqual(weeks_in_month(2, 2025), 4)

    def test_maerz_2025_hat_5_wochen(self):
        """Mär 2025 (31d, startet Sa, endet Mo) → 5"""
        self.assertEqual(weeks_in_month(3, 2025), 5)

    def test_februar_2024_schaltjahr_5_wochen(self):
        """Feb 2024 (29d, startet Do) → 5"""
        self.assertEqual(weeks_in_month(2, 2024), 5)


class TestWeeklyPlanSkeleton(unittest.TestCase):
    """Regel 2, 4, 5: Wochenplan-Struktur und CookOnce"""

    def setUp(self):
        self.rids = [uuid.uuid4() for _ in range(10)]

    def test_wochenplan_hat_7_dinner_slots(self):
        """Plan hat Mo-So je 1 Dinner."""
        plan = generate_weekly_plan_skeleton(1, None, self.rids)
        dinners = [s for s in plan["meal_slots"] if s["meal_type"] == "dinner"]
        self.assertEqual(len(dinners), 7)

    def test_cook_once_erzeugt_repeat_slots(self):
        """2 CookOnce-Rezepte → 2 zusätzliche Repeat-Slots."""
        cook_once = self.rids[:2]
        plan = generate_weekly_plan_skeleton(1, None, self.rids, cook_once)
        repeats = [s for s in plan["meal_slots"] if s["is_repeat"]]
        self.assertEqual(len(repeats), 2)

    def test_kein_rezept_wiederholt_sich(self):
        """Kein Rezept-ID mehrfach (außer als Repeat markiert)."""
        plan = generate_weekly_plan_skeleton(1, None, self.rids)
        used = set()
        for s in plan["meal_slots"]:
            if not s["is_repeat"]:
                self.assertNotIn(s["recipe_id"], used)
                used.add(s["recipe_id"])


class TestMonthlyPlanGenerator(unittest.TestCase):
    """Regel 1, 3: Monatsplan"""

    def setUp(self):
        self.config = GeneratorConfig(
            household_id=uuid.uuid4(),
            month=3,
            year=2025,
            member_ids=[uuid.uuid4() for _ in range(2)],
            recipe_ids=SAMPLE_RECIPE_IDS,
            cook_once_eat_twice_count=2,
            meals_per_week=5,
        )

    def test_anzahl_wochen_4_oder_5(self):
        """Monatsplan hat 4 oder 5 Wochen."""
        plan = generate_monthly_plan(self.config)
        self.assertIn(len(plan["weeks"]), (4, 5),
                      f"März 2025 hat {len(plan['weeks'])} Wochen")

    def test_wochen_sind_nummeriert(self):
        """Wochen 1..N."""
        plan = generate_monthly_plan(self.config)
        for i, w in enumerate(plan["weeks"], start=1):
            self.assertEqual(w["week_number"], i)


# ─── Grocery-Engine Tests ──────────────────────────────────────────────────

class TestGroceryListBuilding(unittest.TestCase):
    """Grundlegende Einkaufslistenerstellung – mit setUp-Isolation."""

    def setUp(self):
        _RECIPE_CACHE.clear()
        # Standard-Rezepte registrieren
        register_dummy_recipe(RID_A, [
            {"ingredient_id": CID, "quantity": 3.0,   "unit": "Stück", "substitution_note": None},
            {"ingredient_id": MID, "quantity": 200.0,  "unit": "ml",    "substitution_note": "Hafermilch"},
        ])
        register_dummy_recipe(RID_B, [
            {"ingredient_id": PID, "quantity": 500.0,  "unit": "g",     "substitution_note": None},
            {"ingredient_id": HID, "quantity": 2.0,    "unit": "Stück", "substitution_note": None},
        ])

    def test_ein_gericht_zwei_zutaten(self):
        """Rezept A → 2 Zutaten."""
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        self.assertEqual(len(result["items"]), 2)

    def test_zwei_gerichte_vier_zutaten(self):
        """Rezepte A+B → 4 verschiedene Zutaten."""
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        names = {i["name"] for i in result["items"]}
        self.assertIn("Karotten",    names)
        self.assertIn("Kartoffeln",  names)
        self.assertIn("Hähnchenbrust", names)
        self.assertIn("Sahne",       names)

    def test_cook_once_repeat_wird_ignoriert(self):
        """Repeat-Slot zählt nicht in die Summe."""
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": True},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        sahne = [i for i in result["items"] if i["name"] == "Sahne"][0]
        self.assertEqual(sahne["total_quantity"], 200.0)

    def test_gruppierung_nach_kategorie(self):
        """Grouped-Result enthält Kategorie-Schlüssel."""
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        self.assertIn("vegetables", result["grouped"])
        self.assertIn("meat",       result["grouped"])
        self.assertIn("dairy",      result["grouped"])

    def test_summiert_gleiche_zutat(self):
        """Gleiche Zutat aus 2 Rezepten → Summe."""
        # Rezept A bekommt zusätzlich Kartoffeln
        _RECIPE_CACHE[RID_A] = [
            {"ingredient_id": CID, "quantity": 3.0,   "unit": "Stück", "substitution_note": None},
            {"ingredient_id": PID, "quantity": 250.0,  "unit": "g",     "substitution_note": None},
        ]
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
            {"recipe_id": RID_B, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        kartoffeln = [i for i in result["items"] if i["name"] == "Kartoffeln"][0]
        self.assertEqual(kartoffeln["total_quantity"], 750.0)  # 250 + 500

    def test_servings_multiplier_skaliert(self):
        """1.5× Portionen → 1.5× Menge."""
        _RECIPE_CACHE[RID_A] = [
            {"ingredient_id": CID, "quantity": 3.0, "unit": "Stück", "substitution_note": None},
        ]
        plan = {"meal_slots": [
            {"recipe_id": RID_A, "meal_type": "dinner", "servings_multiplier": 1.5, "is_repeat": False},
        ]}
        result = build_grocery_list(plan, INGREDIENTS)
        karotten = [i for i in result["items"] if i["name"] == "Karotten"][0]
        self.assertEqual(karotten["total_quantity"], 4.5)  # 3 × 1.5


if __name__ == "__main__":
    unittest.main(verbosity=2)