#!/usr/bin/env python3
"""Sprossa – Cleanup: doppelte Monatspläne entfernen + Kalenderwochen korrigieren.

Zwei Probleme aus dem Demo-Account-Feedback (Tasks 60/61):

1. Doppelte Monatspläne: `POST /plans/generate` hat vor dem Upsert-Fix bei jedem
   Aufruf einen NEUEN MonthlyPlan angelegt. Ergebnis: mehrere Pläne für denselben
   (household_id, month, year). Pro Kombination bleibt der Plan mit den meisten
   MealSlots (bei Gleichstand der neueste) erhalten, alle anderen werden in
   FK-konformer Reihenfolge gelöscht:
       grocery_items -> grocery_lists -> meal_slots -> weekly_plans -> monthly_plans

2. Falsche Kalenderwochen: `grocery_lists.week_number` enthielt den internen
   Wochenzähler (1..5) statt der ISO-Kalenderwoche. Korrektur: die Woche des
   verknüpften WeeklyPlans (per monthly_plan_id + week_number) wird auf
   `start_date.isocalendar()[1]` gesetzt. Wo keine Zuordnung möglich ist, bleibt
   der Wert unverändert (und wird gemeldet).

Aufruf:
    python3 scripts/cleanup_plans_and_weeks.py --dry-run
    python3 scripts/cleanup_plans_and_weeks.py --apply
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://sprossa:sprossa@localhost:5433/sprossa_test",
)


def fetch_plan_groups(cur) -> dict[tuple[str, int, int], list[dict]]:
    """Alle Monatspläne gruppiert nach (household_id, month, year)."""
    cur.execute(
        """
        SELECT mp.id, mp.household_id, mp.month, mp.year, mp.generated_at,
               (SELECT count(*) FROM meal_slots ms
                  JOIN weekly_plans wp ON wp.id = ms.weekly_plan_id
                 WHERE wp.monthly_plan_id = mp.id) AS slot_count
          FROM monthly_plans mp
         ORDER BY mp.household_id, mp.year, mp.month, mp.generated_at DESC
        """
    )
    groups: dict[tuple[str, int, int], list[dict]] = defaultdict(list)
    for row in cur.fetchall():
        pid, hh, month, year, generated_at, slot_count = row
        groups[(str(hh), month, year)].append(
            {
                "id": str(pid),
                "generated_at": generated_at,
                "slot_count": slot_count,
            }
        )
    return groups


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Änderungen schreiben")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen (Default)")
    args = ap.parse_args()
    apply = args.apply

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            groups = fetch_plan_groups(cur)

            print("=== 1) Doppelte Monatspläne ===")
            dup_total = 0
            to_delete: list[str] = []
            for (hh, month, year), plans in sorted(groups.items()):
                if len(plans) <= 1:
                    continue
                # Behalte den Plan mit den meisten Slots, bei Gleichstand den neuesten
                plans_sorted = sorted(
                    plans, key=lambda p: (p["slot_count"], p["generated_at"]), reverse=True
                )
                keep, drop = plans_sorted[0], plans_sorted[1:]
                print(
                    f"  {year}-{month:02d} ({hh[:8]}): {len(plans)} Pläne -> "
                    f"behalte {keep['id'][:8]} ({keep['slot_count']} Slots), "
                    f"lösche {len(drop)}"
                )
                to_delete.extend(p["id"] for p in drop)
                dup_total += len(drop)

            if not to_delete:
                print("  keine Duplikate gefunden.")
            elif apply:
                # FK-konforme Reihenfolge
                cur.execute(
                    """
                    DELETE FROM grocery_items WHERE grocery_list_id IN (
                        SELECT id FROM grocery_lists WHERE monthly_plan_id = ANY(%s)
                    )
                    """,
                    (to_delete,),
                )
                gi = cur.rowcount
                cur.execute(
                    "DELETE FROM grocery_lists WHERE monthly_plan_id = ANY(%s)",
                    (to_delete,),
                )
                gl = cur.rowcount
                cur.execute(
                    """
                    DELETE FROM meal_slots WHERE weekly_plan_id IN (
                        SELECT id FROM weekly_plans WHERE monthly_plan_id = ANY(%s)
                    )
                    """,
                    (to_delete,),
                )
                ms = cur.rowcount
                cur.execute(
                    "DELETE FROM weekly_plans WHERE monthly_plan_id = ANY(%s)",
                    (to_delete,),
                )
                wp = cur.rowcount
                cur.execute("DELETE FROM monthly_plans WHERE id = ANY(%s)", (to_delete,))
                mp = cur.rowcount
                print(
                    f"  gelöscht: {gi} GroceryItems, {gl} GroceryLists, "
                    f"{ms} MealSlots, {wp} WeeklyPlans, {mp} MonthlyPlans"
                )
            else:
                print(f"  (dry-run) würde {dup_total} Pläne + zugehörige Daten löschen")

            print("\n=== 2) Kalenderwochen korrigieren ===")
            cur.execute(
                """
                SELECT gl.id, gl.week_number, gl.monthly_plan_id, wp.week_number,
                       wp.start_date
                  FROM grocery_lists gl
                  JOIN weekly_plans wp
                    ON wp.monthly_plan_id = gl.monthly_plan_id
                   AND wp.week_number = gl.week_number
                 WHERE gl.week_number IS NOT NULL
                """
            )
            rows = cur.fetchall()
            updates: list[tuple[int, str]] = []
            unmapped = 0
            for gl_id, gl_week, mpid, wp_week, start_date in rows:
                if not start_date:
                    unmapped += 1
                    continue
                iso_kw = start_date.isocalendar()[1]
                if iso_kw != gl_week:
                    updates.append((iso_kw, str(gl_id)))

            print(f"  {len(rows)} Listen geprüft, {len(updates)} zu korrigieren, "
                  f"{unmapped} ohne Zuordnung")
            if updates:
                sample = ", ".join(f"{w}" for w, _ in updates[:12])
                print(f"  neue KW-Werte (Auszug): {sample}")
                if apply:
                    for iso_kw, gl_id in updates:
                        cur.execute(
                            "UPDATE grocery_lists SET week_number = %s WHERE id = %s",
                            (iso_kw, gl_id),
                        )
                    print(f"  {len(updates)} Listen aktualisiert.")
                else:
                    print("  (dry-run) keine Änderungen geschrieben")

        if apply:
            conn.commit()
            print("\n✅ Änderungen committet.")
        else:
            conn.rollback()
            print("\n(dry-run – keine Änderungen geschrieben)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
