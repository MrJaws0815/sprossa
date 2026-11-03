#!/usr/bin/env python3
"""Sprossa – Platzhalter-/Demo-Rezepte aus Katalog und Plänen entfernen.

Problem:
    26 Demo-Rezepte („Testrezept 1–6“, „Rezept A/B/C“, „Einziges Rezept“) aus
    den Haushalten „Test-Plan-Haushalt“ / „Swap-Test-Haushalt-*“ liegen im
    GLOBALEN Rezept-Katalog. Neue Nutzer bekommen sie dadurch in ihre Pläne;
    bestehende MealSlots referenzieren sie.

Fix (in dieser Reihenfolge):
    1. Platzhalter-Rezepte anhand des Titels ermitteln (case-insensitive).
    2. MealSlots finden, die auf diese Rezepte zeigen.
    3. Self-FK meal_slots.original_meal_slot_id auf NULL setzen, wo er auf
       einen zu löschenden Slot zeigt (sonst FK-Verletzung).
    4. Diese MealSlots löschen.
    5. recipes.leftover_recipe_id auf NULL setzen, wo er auf Platzhalter zeigt.
    6. recipe_ingredients der Platzhalter löschen.
    7. Platzhalter-Rezepte löschen.
    8. Alle WeeklyPlans ohne verbleibende MealSlots ermitteln; deren
       MonthlyPlans auf status='draft' setzen (nicht löschen), damit der
       Nutzer neu generieren kann.

Aufruf:
    python3 scripts/purge_placeholder_recipes.py --dry-run   # Default
    python3 scripts/purge_placeholder_recipes.py --apply
"""
from __future__ import annotations

import argparse
import os
import sys

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    os.environ.get(
        "MM_DATABASE_URL_SYNC",
        "postgresql://sprossa:sprossa@localhost:5433/sprossa_test",
    ),
)

# Gleiche Blacklist wie app/services/plan_generator.py
PLACEHOLDER_PATTERNS = (
    "testrezept",
    "rezept a",
    "rezept b",
    "rezept c",
    "einziges rezept",
)

# SQL-Filter, der exakt der Python-Logik entspricht:
#   startswith "testrezept" OR contains "einziges rezept"
#   OR startswith "rezept a" / "rezept b" / "rezept c"
PLACEHOLDER_SQL = """
    lower(btrim(r.title)) LIKE 'testrezept%%'
    OR lower(btrim(r.title)) LIKE '%%einziges rezept%%'
    OR lower(btrim(r.title)) LIKE 'rezept a%%'
    OR lower(btrim(r.title)) LIKE 'rezept b%%'
    OR lower(btrim(r.title)) LIKE 'rezept c%%'
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Änderungen schreiben")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen (Default)")
    args = ap.parse_args()
    apply = args.apply

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            # 1) Platzhalter-Rezepte
            cur.execute(
                f"SELECT r.id, r.title, r.household_id, h.name "
                f"FROM recipes r JOIN households h ON h.id = r.household_id "
                f"WHERE {PLACEHOLDER_SQL} ORDER BY r.title;"
            )
            placeholders = cur.fetchall()
            placeholder_ids = [str(row[0]) for row in placeholders]

            print(f"=== Platzhalter-Rezepte: {len(placeholders)} ===")
            for _id, title, _hh, hh_name in placeholders:
                print(f"  {title!r}  (Haushalt: {hh_name})")

            if not placeholder_ids:
                print("  keine Platzhalter gefunden – nichts zu tun.")
                return 0

            # 2) Betroffene MealSlots
            cur.execute(
                "SELECT count(*) FROM meal_slots WHERE recipe_id = ANY(%s);",
                (placeholder_ids,),
            )
            slot_count = cur.fetchone()[0]

            # Betroffene WeeklyPlans / MonthlyPlans (vor dem Löschen)
            cur.execute(
                """
                SELECT count(DISTINCT wp.monthly_plan_id)
                  FROM meal_slots ms
                  JOIN weekly_plans wp ON wp.id = ms.weekly_plan_id
                 WHERE ms.recipe_id = ANY(%s);
                """,
                (placeholder_ids,),
            )
            affected_plans = cur.fetchone()[0]

            # Self-FK-Kandidaten
            cur.execute(
                "SELECT count(*) FROM meal_slots "
                "WHERE original_meal_slot_id IN (SELECT id FROM meal_slots WHERE recipe_id = ANY(%s));",
                (placeholder_ids,),
            )
            self_fk_count = cur.fetchone()[0]

            # Rezepte, die per leftover_recipe_id auf Platzhalter zeigen
            cur.execute(
                "SELECT count(*) FROM recipes WHERE leftover_recipe_id = ANY(%s);",
                (placeholder_ids,),
            )
            leftover_refs = cur.fetchone()[0]

            # recipe_ingredients der Platzhalter
            cur.execute(
                "SELECT count(*) FROM recipe_ingredients WHERE recipe_id = ANY(%s);",
                (placeholder_ids,),
            )
            ri_count = cur.fetchone()[0]

            print(
                f"  -> {slot_count} MealSlots, {affected_plans} betroffene MonthlyPlans, "
                f"{self_fk_count} Self-FK-Referenzen, {leftover_refs} leftover-Referenzen, "
                f"{ri_count} RecipeIngredients."
            )

            # 3) Wochen, die nach dem Löschen leer sind
            #    (nur Wochen, die aktuell Platzhalter-Slots haben – andere Wochen
            #     wurden nicht angefasst und bleiben unberücksichtigt.)
            cur.execute(
                """
                SELECT DISTINCT wp.id, wp.monthly_plan_id, wp.week_number,
                       (SELECT count(*) FROM meal_slots ms2
                         WHERE ms2.weekly_plan_id = wp.id
                           AND ms2.recipe_id <> ALL(%s)) AS remaining
                  FROM weekly_plans wp
                  JOIN meal_slots ms ON ms.weekly_plan_id = wp.id
                 WHERE ms.recipe_id = ANY(%s)
                 ORDER BY wp.monthly_plan_id, wp.week_number;
                """,
                (placeholder_ids, placeholder_ids),
            )
            week_rows = cur.fetchall()
            empty_weeks = [row for row in week_rows if row[3] == 0]
            plans_to_draft = sorted({str(row[1]) for row in empty_weeks})

            print(f"\n=== Leere Wochen nach Bereinigung: {len(empty_weeks)} ===")
            for wp_id, mp_id, week_no, _rem in empty_weeks:
                print(f"  WeeklyPlan {str(wp_id)[:8]} (Plan {str(mp_id)[:8]}, Woche {week_no})")
            print(f"  -> {len(plans_to_draft)} MonthlyPlans würden auf 'draft' gesetzt.")

            if not apply:
                print("\n(dry-run) Keine Änderungen geschrieben.")
                conn.rollback()
                return 0

            # ── APPLY ──────────────────────────────────────────────────────
            cur.execute(
                """
                UPDATE meal_slots SET original_meal_slot_id = NULL
                 WHERE original_meal_slot_id IN (
                     SELECT id FROM meal_slots WHERE recipe_id = ANY(%s)
                 );
                """,
                (placeholder_ids,),
            )
            fk_nulled = cur.rowcount

            cur.execute("DELETE FROM meal_slots WHERE recipe_id = ANY(%s);", (placeholder_ids,))
            slots_deleted = cur.rowcount

            cur.execute(
                "UPDATE recipes SET leftover_recipe_id = NULL WHERE leftover_recipe_id = ANY(%s);",
                (placeholder_ids,),
            )
            leftover_nulled = cur.rowcount

            cur.execute(
                "DELETE FROM recipe_ingredients WHERE recipe_id = ANY(%s);",
                (placeholder_ids,),
            )
            ri_deleted = cur.rowcount

            cur.execute("DELETE FROM recipes WHERE id = ANY(%s);", (placeholder_ids,))
            recipes_deleted = cur.rowcount

            # Nach dem Löschen erneut prüfen: jetzt können weitere Wochen leer sein,
            # weil Self-FK-/Kaskaden nichts nachzieht. Gleiche Abfrage wie oben.
            cur.execute(
                """
                SELECT DISTINCT wp.monthly_plan_id
                  FROM weekly_plans wp
                 WHERE NOT EXISTS (
                     SELECT 1 FROM meal_slots ms WHERE ms.weekly_plan_id = wp.id
                 );
                """
            )
            empty_week_plans = [str(row[0]) for row in cur.fetchall()]

            cur.execute(
                "UPDATE monthly_plans SET status = 'draft' WHERE id = ANY(%s);",
                (empty_week_plans,),
            )
            plans_drafted = cur.rowcount

            conn.commit()
            print(
                f"\n✅ Bereinigt: {slots_deleted} MealSlots gelöscht "
                f"({fk_nulled} Self-FK auf NULL), {leftover_nulled} leftover-Referenzen "
                f"genullt, {ri_deleted} RecipeIngredients, {recipes_deleted} Rezepte gelöscht."
            )
            print(
                f"   {plans_drafted} MonthlyPlans mit leeren Wochen auf 'draft' gesetzt "
                f"({len(empty_week_plans)} Kandidaten geprüft)."
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
