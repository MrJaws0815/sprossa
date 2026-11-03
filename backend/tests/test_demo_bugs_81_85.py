"""Regressionstests fuer die Demo-Bugs Task 81-85.

Abgedeckt:
- Task 81: Zutaten-Varianten werden in der Einkaufsliste gruppiert
  (Rezept-Zutaten bleiben unveraendert).
- Task 82: Supermarkt-spezifische Gang-Reihenfolge (Rewe vs. Aldi).
- Task 83: Cook-once-Eat-twice wird pro Woche erzwungen (bzw. abschaltbar).
- Task 85: shopping_days unterteilt die Wochenliste in Segmente.
"""
from datetime import date
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.services.grocery_engine import (
    _group_key,
    build_export_txt,
    build_grocery_list,
    get_gang_order,
    register_dummy_recipe,
)
from app.services.plan_generator import (
    _segment_slots_by_shopping_days,
    generate_balanced_weekly_slots,
)


# ─── Task 81 – Varianten-Gruppierung ───────────────────────────────────────

def _ing(ingredient_id: str, name: str, category: str = "Gemüse"):
    return {UUID(ingredient_id): {"name": name, "category": category}}


def test_group_key_kartoffel_varianten():
    assert _group_key("Kartoffeln", "Gemüse") == "Kartoffeln"
    assert _group_key("Kartoffeln (festkochend)", "Gemüse") == "Kartoffeln"
    assert _group_key("Kartoffeln (mehligkochend)", "Gemüse") == "Kartoffeln"
    assert _group_key("Junge Kartoffeln", "Gemüse") == "Kartoffeln"
    # Süsskartoffeln sind eine eigene Gruppe
    assert _group_key("Süsskartoffeln", "Gemüse") == "Süsskartoffeln"
    # Vorrat-Kartoffelprodukte bleiben eigenständig (kein Match → Originalname)
    assert _group_key("Kartoffelklöße (halb)", "Vorrat & Konserven") == "Kartoffelklöße (halb)"


def test_zwei_rezepte_kartoffel_varianten_ergeben_eine_zeile():
    """2 Rezepte mit Kartoffeln + Kartoffeln (festkochend) → 1 Listenzeile."""
    base_id = "00000000-0000-0000-0000-000000000201"
    fest_id = "00000000-0000-0000-0000-000000000202"
    ingredients = {
        UUID(base_id): {"name": "Kartoffeln", "category": "Gemüse"},
        UUID(fest_id): {"name": "Kartoffeln (festkochend)", "category": "Gemüse"},
    }
    r1, r2 = uuid4(), uuid4()
    register_dummy_recipe(r1, [{
        "ingredient_id": UUID(base_id), "quantity": 500.0, "unit": "g",
        "substitution_note": None,
    }])
    register_dummy_recipe(r2, [{
        "ingredient_id": UUID(fest_id), "quantity": 300.0, "unit": "g",
        "substitution_note": None,
    }])

    plan = {"meal_slots": [
        {"recipe_id": r1, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        {"recipe_id": r2, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
    ]}
    result = build_grocery_list(plan, ingredients)
    kartoffeln = [i for i in result["items"] if "Kartoffeln" in i["name"]]
    assert len(kartoffeln) == 1, f"Erwartet 1 Zeile, bekommen: {kartoffeln}"
    assert kartoffeln[0]["total_quantity"] == 800.0
    assert "festkochend" in kartoffeln[0]["name"]


def test_verschiedene_einheiten_werden_nicht_summiert():
    """500 g + 2 Stück → zwei Zeilen (unit-aware)."""
    g_id = "00000000-0000-0000-0000-000000000211"
    st_id = "00000000-0000-0000-0000-000000000212"
    ingredients = {
        UUID(g_id): {"name": "Kartoffeln", "category": "Gemüse"},
        UUID(st_id): {"name": "Kartoffeln (festkochend)", "category": "Gemüse"},
    }
    r1, r2 = uuid4(), uuid4()
    register_dummy_recipe(r1, [{"ingredient_id": UUID(g_id), "quantity": 500.0, "unit": "g", "substitution_note": None}])
    register_dummy_recipe(r2, [{"ingredient_id": UUID(st_id), "quantity": 2.0, "unit": "Stück", "substitution_note": None}])
    plan = {"meal_slots": [
        {"recipe_id": r1, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        {"recipe_id": r2, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
    ]}
    result = build_grocery_list(plan, ingredients)
    kartoffeln = [i for i in result["items"] if "Kartoffeln" in i["name"]]
    assert len(kartoffeln) == 2
    assert {i["unit"] for i in kartoffeln} == {"g", "Stück"}


# ─── Task 82 – Supermarkt-spezifische Gang-Reihenfolge ─────────────────────

def test_get_gang_order_unterscheidet_supermaerkte():
    rewe = [label for label, _ in get_gang_order("rewe")]
    aldi = [label for label, _ in get_gang_order("aldi")]
    edeka = [label for label, _ in get_gang_order("edeka")]
    lidl = [label for label, _ in get_gang_order("lidl")]
    assert rewe[0] == "Gemüse"
    assert aldi[0] == "Backwaren"
    assert edeka[0] == "Obst"
    assert lidl[0] == "Backwaren"
    # Unbekannt → Rewe-Fallback
    assert [label for label, _ in get_gang_order("unbekannt")] == rewe
    assert [label for label, _ in get_gang_order(None)] == rewe


def test_export_txt_rewe_vs_aldi_andere_reihenfolge():
    rows = [
        {"quantity": "1", "unit": "kg", "name": "Kartoffeln", "category": "Gemüse", "gang": "Gemüse", "notes": None},
        {"quantity": "2", "unit": "Stück", "name": "Brot", "category": "Backwaren", "gang": "Backwaren", "notes": None},
    ]
    rewe_txt = build_export_txt(rows, week_number=12, supermarket="rewe")
    aldi_txt = build_export_txt(rows, week_number=12, supermarket="aldi")
    rewe_heads = [line for line in rewe_txt.splitlines() if line.startswith("==")]
    aldi_heads = [line for line in aldi_txt.splitlines() if line.startswith("==")]
    assert rewe_heads[0] == "== Gemüse =="
    assert aldi_heads[0] == "== Backwaren =="
    assert rewe_heads != aldi_heads


# ─── Task 83 – Cook-once-Eat-twice erzwingen ───────────────────────────────

def _recipe(title: str, cook_once: bool = False):
    return SimpleNamespace(
        id=uuid4(), title=title, tags=[], servings=4,
        cook_once_eat_twice=cook_once,
    )


def test_cook_once_enabled_erzwingt_repeat_slots():
    recipes = [_recipe(f"Gericht {i}", cook_once=(i < 4)) for i in range(12)]
    cook_ids = [r.id for r in recipes if r.cook_once_eat_twice]
    recipe_map = {r.id: r for r in recipes}

    slots = generate_balanced_weekly_slots(
        week_number=1, start_date=date(2026, 10, 1),
        available_recipes=recipes, cook_once_ids=cook_ids,
        recipe_map=recipe_map, total_portions=1.0,
        cook_once_enabled=True, cook_once_count=2,
    )
    repeats = [s for s in slots if s["is_repeat"]]
    assert len(repeats) >= 1, "CookOnce muss mindestens einen Repeat-Slot erzeugen"
    # Repeat liegt an Tag+2 des Original-Slots
    for rep in repeats:
        originals = [
            s for s in slots
            if not s["is_repeat"] and s["recipe_id"] == rep["recipe_id"]
        ]
        assert originals, "Repeat-Slot muss ein Original haben"
        assert rep["day_of_week"] == originals[0]["day_of_week"] + 2


def test_cook_once_disabled_erzeugt_keine_repeat_slots():
    recipes = [_recipe(f"Gericht {i}", cook_once=(i < 4)) for i in range(12)]
    cook_ids = [r.id for r in recipes if r.cook_once_eat_twice]
    recipe_map = {r.id: r for r in recipes}

    slots = generate_balanced_weekly_slots(
        week_number=1, start_date=date(2026, 10, 1),
        available_recipes=recipes, cook_once_ids=cook_ids,
        recipe_map=recipe_map, total_portions=1.0,
        cook_once_enabled=False, cook_once_count=2,
    )
    assert [s for s in slots if s["is_repeat"]] == []


# ─── Task 85 – Einkaufs-Segmentierung ──────────────────────────────────────

def _slot(day: int):
    return SimpleNamespace(day_of_week=day)


def test_segmentierung_nach_einkaufstagen_1_4():
    slots = [_slot(d) for d in range(1, 8)]
    segments = _segment_slots_by_shopping_days(slots, [1, 4])
    assert len(segments) == 2
    labels = [label for label, _ in segments]
    assert labels[0] == "Einkauf Mo bis Mi"
    assert labels[1] == "Einkauf Do bis So"
    assert [s.day_of_week for s in segments[0][1]] == [1, 2, 3]
    assert [s.day_of_week for s in segments[1][1]] == [4, 5, 6, 7]


def test_segmentierung_ohne_shopping_days_ein_segment():
    slots = [_slot(d) for d in range(1, 8)]
    segments = _segment_slots_by_shopping_days(slots, [])
    assert len(segments) == 1
    assert len(segments[0][1]) == 7
