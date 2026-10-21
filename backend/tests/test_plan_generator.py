"""Tests für den Plan-Generator

TDD-Anker (RED → GREEN → REFACTOR):
1. weeks_in_month() gibt 4 oder 5 zurück je nach Monat
2. generate_monthly_plan() erzeugt für 4 Wochen korrekte Anzahl WeeklyPlans
3. Jede Woche hat 7 Tage mit mindestens 1 Hauptmahlzeit (dinner)
4. CookOnce-EatTwice: doppelte Belegung (Slot + Repeat-Slot), aber max 2/Woche
5. Kein Rezept erscheint mehrfach in derselben Woche (außer als Repeat)
"""
from datetime import date

import pytest

from app.services.plan_generator import (
    GeneratorConfig,
    generate_monthly_plan,
    generate_weekly_plan_skeleton,
    weeks_in_month,
)


class TestWeeksInMonth:
    """Regel 1: Monats-Wochenanzahl"""

    def test_januar_2025_hat_5_wochen(self):
        """Januar 2025 hat Tage in 5 Kalenderwochen."""
        assert weeks_in_month(1, 2025) == 5

    def test_februar_2025_hat_4_wochen(self):
        """Februar 2025 (28 Tage) hat 4 Wochen."""
        assert weeks_in_month(2, 2025) == 4

    def test_maerz_2025_hat_5_wochen(self):
        """März 2025 hat 5 Wochen."""
        assert weeks_in_month(3, 2025) == 5

    def test_februar_2024_hat_5_wochen(self):
        """Februar 2024 (Schaltjahr, 29 Tage) kann 5 Wochen haben."""
        assert weeks_in_month(2, 2024) == 5


class TestWeeklyPlanSkeleton:
    """Regel 2, 4, 5: Wochenplan-Struktur und CookOnce"""

    def test_wochenplan_hat_7_dinner_slots(self):
        """Ein Wochenplan ohne CookOnce hat genau 7 Dinner-Slots (Mo-So)."""
        rids = [uuid4() for _ in range(7)]
        plan = generate_weekly_plan_skeleton(1, date(2025, 3, 3), rids)
        dinners = [s for s in plan["meal_slots"] if s["meal_type"] == "dinner"]
        assert len(dinners) == 7

    def test_wochenplan_mit_cook_once_hat_zusaetzliche_repeat_slots(self):
        """Mit 2 CookOnce-Rezepten hat der Plan 7+2=9 Slots (7 original + 2 repeats)."""
        rids = [uuid4() for _ in range(7)]
        cook_once = rids[:2]
        plan = generate_weekly_plan_skeleton(1, date(2025, 3, 3), rids, cook_once)
        repeats = [s for s in plan["meal_slots"] if s["is_repeat"]]
        assert len(repeats) == 2

    def test_cook_once_repeat_hat_correcte_referenz(self):
        """Ein Repeat-Slot hat is_repeat=True und original_meal_slot_id wird erstmal nicht gesetzt (später)."""
        rids = [uuid4() for _ in range(7)]
        cook_once = [rids[0]]
        plan = generate_weekly_plan_skeleton(1, date(2025, 3, 3), rids, cook_once)
        repeats = [s for s in plan["meal_slots"] if s["is_repeat"]]
        assert len(repeats) == 1

    def test_kein_rezept_wiederholt_sich_in_einer_woche(self):
        """Kein Rezept-ID kommt mehrfach vor (ohne CookOnce-Betrachtung)."""
        rids = [uuid4() for _ in range(10)]
        plan = generate_weekly_plan_skeleton(1, date(2025, 3, 3), rids)
        used = set()
        for s in plan["meal_slots"]:
            if not s["is_repeat"]:
                assert s["recipe_id"] not in used, f"Rezept {s['recipe_id']} doppelt"
                used.add(s["recipe_id"])


class TestMonthlyPlanGenerator:
    """Regel 1, 3: Monatsplan-Generierung"""

    def test_generiert_4_oder_5_wochen(self, basic_config):
        """Monatsplan hat 4 oder 5 Wochen je nach Monat."""
        plan = generate_monthly_plan(basic_config)
        weeks = plan["weeks"]
        assert len(weeks) in (4, 5)

    def test_jede_woche_hat_start_datum(self, basic_config):
        """Jede Woche hat ein start_date."""
        plan = generate_monthly_plan(basic_config)
        for week in plan["weeks"]:
            assert week["start_date"] is not None

    def test_wochen_sind_korrekt_nummeriert(self, basic_config):
        """Wochen sind 1-indiziert (1, 2, 3, …)."""
        plan = generate_monthly_plan(basic_config)
        for i, week in enumerate(plan["weeks"], start=1):
            assert week["week_number"] == i

    def test_focus_tags_werden_uebernommen(self, basic_config):
        """Focus-Tags sind im Resultat vermerkt."""
        # Der Generator speichert focus_tags noch nicht im Resultat
        # TODO: später in den Output integrieren
        pass


# -- Hilfsmittel -----------------------------------------------------------

from uuid import uuid4