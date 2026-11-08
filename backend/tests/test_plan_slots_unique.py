"""Regressionstest: Kein Wochentag darf zwei Abendessen haben.

Bug (gemeldet aus der Beta): In KW44/45 stand zweimal Mittwoch im Plan,
in KW46 mehrfach Montag und Donnerstag. Ursache: Der Cook-Once-Repeat-Slot
wurde an Tag+2 ZUSAETZLICH angehaengt, statt den regulaeren Slot dort zu
ersetzen. Ergebnis: 48 Slots statt 35 in einem Fuenf-Wochen-Monat.
"""
import uuid
from datetime import date

from app.services.plan_generator import generate_balanced_weekly_slots


class FakeRecipe:
    def __init__(self, n: int, cook_once: bool = False):
        self.id = uuid.uuid4()
        self.title = f"Gericht {n}"
        self.servings = 4.0
        self.cook_once_eat_twice = cook_once


def _slots(cook_once_count: int = 3):
    recipes = [FakeRecipe(i, cook_once=(i < cook_once_count)) for i in range(20)]
    cook_once_ids = [r.id for r in recipes if r.cook_once_eat_twice]
    return generate_balanced_weekly_slots(
        week_number=45,
        start_date=date(2026, 11, 2),
        available_recipes=recipes,
        cook_once_ids=cook_once_ids,
        recipe_map={r.id: r for r in recipes},
        total_portions=4.0,
        cook_once_enabled=True,
        cook_once_count=cook_once_count,
    )


def test_jeder_tag_genau_ein_slot():
    slots = _slots()
    pro_tag: dict[int, int] = {}
    for s in slots:
        pro_tag[s["day_of_week"]] = pro_tag.get(s["day_of_week"], 0) + 1

    assert len(slots) == 7, f"Genau 7 Abendessen pro Woche erwartet, waren {len(slots)}"
    assert set(pro_tag) == set(range(1, 8)), f"Alle Tage 1-7 erwartet, waren {sorted(pro_tag)}"
    doppelt = {d: c for d, c in pro_tag.items() if c > 1}
    assert not doppelt, f"Tage mit mehr als einem Abendessen: {doppelt}"


def test_slots_sind_nach_tag_sortiert():
    slots = _slots()
    tage = [s["day_of_week"] for s in slots]
    assert tage == sorted(tage), f"Slots nicht nach Wochentag sortiert: {tage}"


def test_cook_once_erzeugt_wiederholung():
    """Cook-Once muss weiterhin wirken - nur eben ersetzend, nicht zusaetzlich."""
    slots = _slots(cook_once_count=2)
    repeats = [s for s in slots if s.get("is_repeat")]
    assert repeats, "Bei aktiviertem Cook-Once muss mindestens ein Repeat-Slot entstehen"

    # Der Repeat darf nicht am selben Tag wie das Original liegen
    original_je_tag = {
        s["day_of_week"]: s["recipe_id"] for s in slots if not s.get("is_repeat")
    }
    for rep in repeats:
        tag = rep["day_of_week"]
        if tag in original_je_tag:
            assert original_je_tag[tag] != rep["recipe_id"], (
                "Repeat und Original duerfen nicht am selben Tag stehen"
            )


def test_ohne_cook_once_keine_repeats():
    slots = _slots(cook_once_count=0)
    assert not [s for s in slots if s.get("is_repeat")]
    assert len(slots) == 7
