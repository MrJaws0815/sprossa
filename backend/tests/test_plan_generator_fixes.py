"""Regressionstests fuer die 6 Kernlogik-Bugs im Plan-Generator.

Deckt ab:
1. Abwechslung: Woche 1 und Woche 2 sind bei genug Rezepten nicht identisch.
2. Saisonalitaet: Oktober filtert Fruehling/Sommer-Rezepte (z.B. Spargel) raus.
3. Monats-Scope: nur aktueller/naechster Monat, sonst ValidationError.
4. Portions-Multiplier: total_portions / recipe.servings.
5. ISO-Kalenderwoche in GroceryLists (DB-Test in test_plan_generator_db.py).
6. Profil-Mismatch: diet_types/type/preferences + Haushalts-Allergien.
"""
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.api import MonthlyPlanCreate
from app.services.plan_generator import (
    _filter_by_diet,
    _filter_by_season,
    calculate_total_portions,
    generate_balanced_weekly_slots,
)


def _recipe(title: str, tags: list[str], servings: int = 4, cook_once: bool = False):
    return SimpleNamespace(
        id=uuid4(),
        title=title,
        tags=tags,
        servings=servings,
        cook_once_eat_twice=cook_once,
    )


def _non_repeat_ids(slots: list[dict]) -> set:
    return {s["recipe_id"] for s in slots if not s["is_repeat"]}


# ── Bug 1: Abwechslung / deterministisches Shuffle ─────────────────────────

def test_woche1_und_woche2_wiederholen_sich_nicht():
    recipes = [
        _recipe(f"Gericht {i}", tags=[]) for i in range(40)
    ]
    week1 = generate_balanced_weekly_slots(
        week_number=1,
        start_date=date(2026, 10, 1),
        available_recipes=recipes,
        cook_once_ids=[],
        recipe_map={r.id: r for r in recipes},
    )
    week2 = generate_balanced_weekly_slots(
        week_number=2,
        start_date=date(2026, 10, 8),
        available_recipes=recipes,
        cook_once_ids=[],
        recipe_map={r.id: r for r in recipes},
        previous_week_ids=_non_repeat_ids(week1),
    )
    assert _non_repeat_ids(week1).isdisjoint(_non_repeat_ids(week2)), (
        "Woche 2 darf keine Rezepte aus Woche 1 wiederholen"
    )


def test_shuffle_ist_deterministisch():
    recipes = [_recipe(f"Gericht {i}", tags=[]) for i in range(40)]
    kwargs = dict(
        week_number=2,
        start_date=date(2026, 10, 8),
        available_recipes=recipes,
        cook_once_ids=[],
        recipe_map={r.id: r for r in recipes},
    )
    first = [s["recipe_id"] for s in generate_balanced_weekly_slots(**kwargs)]
    second = [s["recipe_id"] for s in generate_balanced_weekly_slots(**kwargs)]
    assert first == second, "gleicher Monat + Config muss denselben Plan ergeben"


# ── Bug 2: Saisonalitaet ───────────────────────────────────────────────────

def test_oktober_filtert_fruehling_und_sommer():
    recipes = [
        _recipe("Spargel mit Hollandaise", ["frühling"]),
        _recipe("Sommerlicher Salat", ["sommer"]),
        _recipe("Kuerbissuppe", ["herbst"]),
        _recipe("Ganzjaehriges Gericht", ["saisonal"]),
        _recipe("Neutrales Gericht", []),
    ]
    allowed = _filter_by_season(recipes, month=10)
    titles = {r.title for r in allowed}
    assert "Spargel mit Hollandaise" not in titles
    assert "Sommerlicher Salat" not in titles
    assert "Kuerbissuppe" in titles
    assert "Ganzjaehriges Gericht" in titles
    assert "Neutrales Gericht" in titles


def test_saisonal_allein_ist_immer_erlaubt():
    recipes = [_recipe("Saisonal", ["saisonal"])]
    for month in (1, 4, 7, 10, 12):
        assert _filter_by_season(recipes, month) == recipes


def test_saison_filter_kann_leer_werden():
    recipes = [_recipe("Spargel", ["frühling"]), _recipe("Erdbeeren", ["sommer"])]
    assert _filter_by_season(recipes, month=10) == []


# ── Bug 3: Monats-Scope ────────────────────────────────────────────────────

def test_aktueller_und_naechster_monat_erlaubt():
    today = date.today()
    MonthlyPlanCreate(month=today.month, year=today.year)
    next_month = 1 if today.month == 12 else today.month + 1
    next_year = today.year + 1 if today.month == 12 else today.year
    MonthlyPlanCreate(month=next_month, year=next_year)


def test_uebernaechster_monat_wird_abgelehnt():
    today = date.today()
    if today.month >= 11:
        bad_month, bad_year = today.month - 1, today.year + 1
    else:
        bad_month, bad_year = today.month + 2, today.year
    with pytest.raises(ValidationError) as exc:
        MonthlyPlanCreate(month=bad_month, year=bad_year)
    assert "aktuellen oder naechsten Monat" in str(exc.value)


def test_jahresueberlauf_dezember_zu_januar(monkeypatch):
    """Wenn heute Dezember ist, muss Januar des Folgejahres erlaubt sein."""
    import app.schemas.api as api_module

    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 12, 15)

    monkeypatch.setattr(api_module, "date", FakeDate)
    MonthlyPlanCreate(month=1, year=2027)  # erlaubt
    with pytest.raises(ValidationError):
        MonthlyPlanCreate(month=2, year=2027)  # uebernaechster Monat


# ── Bug 4: Portions-Multiplier ─────────────────────────────────────────────

def test_portion_multiplier_wird_angewendet():
    recipes = [_recipe(f"Gericht {i}", [], servings=4) for i in range(20)]
    slots = generate_balanced_weekly_slots(
        week_number=1,
        start_date=date(2026, 10, 1),
        available_recipes=recipes,
        cook_once_ids=[],
        recipe_map={r.id: r for r in recipes},
        total_portions=2.0,
    )
    assert slots
    for slot in slots:
        assert slot["servings_multiplier"] == pytest.approx(0.5)


def test_portion_multiplier_fallback_ohne_portions():
    recipes = [_recipe("Gericht", [], servings=4)]
    slots = generate_balanced_weekly_slots(
        week_number=1,
        start_date=date(2026, 10, 1),
        available_recipes=recipes,
        cook_once_ids=[],
        recipe_map={r.id: r for r in recipes},
        total_portions=0.0,
    )
    assert slots[0]["servings_multiplier"] == 1.0


def test_portion_multiplier_ohne_servings_ist_1():
    recipe = _recipe("Ohne Portionen", [], servings=0)
    slots = generate_balanced_weekly_slots(
        week_number=1,
        start_date=date(2026, 10, 1),
        available_recipes=[recipe],
        cook_once_ids=[],
        recipe_map={recipe.id: recipe},
        total_portions=3.0,
    )
    assert slots[0]["servings_multiplier"] == 1.0


def test_repeat_slot_hat_gleichen_multiplier():
    recipe = _recipe("CookOnce", [], servings=2, cook_once=True)
    slots = generate_balanced_weekly_slots(
        week_number=1,
        start_date=date(2026, 10, 1),
        available_recipes=[recipe],
        cook_once_ids=[recipe.id],
        recipe_map={recipe.id: recipe},
        total_portions=1.0,
    )
    repeat_slots = [s for s in slots if s["is_repeat"]]
    assert repeat_slots, "CookOnce-Rezept muss Repeat-Slots erzeugen"
    for slot in slots:
        assert slot["servings_multiplier"] == pytest.approx(0.5)


# ── Bug 6: Profil / Ernaehrung / Allergien ─────────────────────────────────

def test_vegetarisch_filtert_fleisch_und_fisch():
    recipes = [
        _recipe("Rindergulasch", ["fleisch"]),
        _recipe("Lachsfilet", ["fisch"]),
        _recipe("Gemuese-Lasagne", ["vegetarisch"]),
        _recipe("Ohne Tags", []),
    ]
    filtered = _filter_by_diet(recipes, {"diet_types": ["vegetarisch"]})
    titles = {r.title for r in filtered}
    assert "Rindergulasch" not in titles
    assert "Lachsfilet" not in titles
    assert "Gemuese-Lasagne" in titles
    assert "Ohne Tags" in titles


def test_vegan_filtert_zusaetzlich_milch_und_eier():
    recipes = [
        _recipe("Kasespaetzle", ["vegetarisch", "milch"]),
        _recipe("Omelette", ["vegetarisch", "eier"]),
        _recipe("Gemuese", ["vegan"]),
    ]
    filtered = _filter_by_diet(recipes, {"diet_types": ["vegan"]})
    titles = {r.title for r in filtered}
    assert "Kasespaetzle" not in titles
    assert "Omelette" not in titles
    assert "Gemuese" in titles


def test_altes_und_neues_profilformat_werden_gelesen():
    recipes = [
        _recipe("Rindergulasch", ["fleisch"]),
        _recipe("Gemuese", ["vegetarisch"]),
    ]
    # altes Format: type (String)
    assert [r.title for r in _filter_by_diet(recipes, {"type": "vegetarisch"})] == ["Gemuese"]
    # preferences (String)
    assert [r.title for r in _filter_by_diet(recipes, {"preferences": "vegetarisch"})] == ["Gemuese"]
    # Unbekannte Keys duerfen nicht crashen
    assert len(_filter_by_diet(recipes, {"unbekannt": ["x"]})) == 2


def test_strengstes_profil_gewinnt():
    recipes = [
        _recipe("Rindergulasch", ["fleisch"]),
        _recipe("Kasespaetzle", ["vegetarisch", "milch"]),
        _recipe("Gemuese", ["vegan"]),
    ]
    # vegetarisch + vegan gemischt -> vegan gewinnt (Kasespaetzle raus)
    filtered = _filter_by_diet(
        recipes, {"diet_types": ["vegetarisch"], "type": "vegan"}
    )
    titles = {r.title for r in filtered}
    assert "Rindergulasch" not in titles
    assert "Kasespaetzle" not in titles
    assert "Gemuese" in titles


def test_portion_factor_aus_dietary_goals_hat_vorrang():
    members = [
        {"age": 30, "dietary_goals": {"portion_factor": 0.5}},
        {"age": 10, "dietary_goals": {}},
        {"age": None, "dietary_goals": {"portion_factor": 1.5}},
    ]
    # 0.5 (gespeichert) + 0.7 (Alter 10) + 1.5 (gespeichert)
    assert calculate_total_portions(members) == pytest.approx(2.7)


def test_portion_factor_fallback_alter():
    members = [{"age": 2}, {"age": 6}, {"age": 10}, {"age": 20}, {"age": None}]
    # 0.3 + 0.5 + 0.7 + 1.0 + 1.0
    assert calculate_total_portions(members) == pytest.approx(3.5)
