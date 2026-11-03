#!/usr/bin/env python3
"""Sprossa – Einkaufslisten-Kalenderwochen korrigieren (ISO-KW statt 1..5).

Problem:
    `grocery_lists.week_number` enthielt den internen Wochenzaehler der
    Plan-Generierung (1..5). Mehrere Listen eines Monats konnten so alle
    week_number=1 tragen, obwohl die zugehoerigen Wochen z. B. ISO-KW 40/41/42
    sind. Ausserdem wurden vor dem Fix nur Listen fuer Woche 1 erzeugt.

Fix:
    Fuer jeden Monatsplan werden die WeeklyPlans nach week_number/start_date
    sortiert. Die (Nicht-Master-)GroceryLists des Plans werden in
    Erzeugungsreihenfolge den Wochen positionell zugeordnet und erhalten
    week_number = start_date.isocalendar()[1] (ISO-KW). Ueberzaehlige Listen
    (Duplikate) werden inkl. ihrer GroceryItems geloescht.

Aufruf:
    python3 scripts/fix_grocery_weeks.py --dry-run   # nur anzeigen (Default)
    python3 scripts/fix_grocery_weeks.py --apply     # schreiben
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


def fetch_plans(cur) -> dict[str, dict]:
    """Alle Monatsplaene mit ihren Wochen und Einkaufslisten laden."""
    cur.execute(
        """
        SELECT id, household_id, month, year
          FROM monthly_plans
         ORDER BY household_id, year, month
        """
    )
    plans: dict[str, dict] = {}
    for pid, hh, month, year in cur.fetchall():
        plans[str(pid)] = {
            "id": str(pid),
            "household": str(hh),
            "month": month,
            "year": year,
            "weeks": [],
            "lists": [],
        }

    cur.execute(
        """
        SELECT id, monthly_plan_id, week_number, start_date
          FROM weekly_plans
         WHERE monthly_plan_id IS NOT NULL
         ORDER BY monthly_plan_id, week_number, start_date
        """
    )
    for wid, mpid, week_number, start_date in cur.fetchall():
        plan = plans.get(str(mpid))
        if plan is not None:
            plan["weeks"].append(
                {
                    "id": str(wid),
                    "week_number": week_number,
                    "start_date": start_date,
                }
            )

    cur.execute(
        """
        SELECT id, monthly_plan_id, week_number, is_master_list, generated_at
          FROM grocery_lists
         WHERE monthly_plan_id IS NOT NULL
         ORDER BY monthly_plan_id, generated_at NULLS FIRST, id
        """
    )
    for gl_id, mpid, week_number, is_master, generated_at in cur.fetchall():
        plan = plans.get(str(mpid))
        if plan is not None:
            plan["lists"].append(
                {
                    "id": str(gl_id),
                    "week_number": week_number,
                    "is_master": bool(is_master),
                    "generated_at": generated_at,
                }
            )
    return plans


def plan_changes(plans: dict[str, dict]):
    """Berechnet Updates und zu loeschende Duplikate."""
    updates: list[tuple[int, str]] = []
    deletes: list[str] = []
    warnings: list[str] = []

    for plan in plans.values():
        weeks = [w for w in plan["weeks"] if w["start_date"] is not None]
        weeks.sort(key=lambda w: (w["week_number"], w["start_date"]))
        lists = [gl for gl in plan["lists"] if not gl["is_master"]]
        if not lists or not weeks:
            continue

        # Master-Listen bleiben unangetastet (week_number bleibt NULL).
        for idx, grocery in enumerate(lists):
            if idx < len(weeks):
                iso_kw = weeks[idx]["start_date"].isocalendar()[1]
                if grocery["week_number"] != iso_kw:
                    updates.append((iso_kw, grocery["id"]))
            else:
                deletes.append(grocery["id"])

        if len(lists) < len(weeks):
            warnings.append(
                f"Plan {plan['id'][:8]} ({plan['year']}-{plan['month']:02d}): "
                f"{len(lists)} Listen fuer {len(weeks)} Wochen"
            )

    return updates, deletes, warnings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Aenderungen schreiben")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen (Default)")
    args = ap.parse_args()
    apply = args.apply

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            plans = fetch_plans(cur)
            updates, deletes, warnings = plan_changes(plans)

            print(f"Monatsplaene geprueft: {len(plans)}")
            print(f"Zu korrigierende Listen: {len(updates)}")
            print(f"Zu loeschende Duplikate: {len(deletes)}")
            for warning in warnings:
                print(f"  HINWEIS: {warning}")

            if updates:
                sample = ", ".join(f"{gl_id[:8]}->KW {kw}" for kw, gl_id in updates[:12])
                print(f"  Beispiele: {sample}")

            if apply and deletes:
                cur.execute(
                    "DELETE FROM grocery_items WHERE grocery_list_id = ANY(%s)",
                    (deletes,),
                )
                gi = cur.rowcount
                cur.execute("DELETE FROM grocery_lists WHERE id = ANY(%s)", (deletes,))
                gl = cur.rowcount
                print(f"  geloescht: {gi} GroceryItems, {gl} GroceryLists")

            if apply and updates:
                for iso_kw, gl_id in updates:
                    cur.execute(
                        "UPDATE grocery_lists SET week_number = %s WHERE id = %s",
                        (iso_kw, gl_id),
                    )
                print(f"  {len(updates)} Listen aktualisiert.")

            if apply:
                conn.commit()
                print("\nOK: Aenderungen committet.")
            else:
                conn.rollback()
                print("\n(dry-run – keine Aenderungen geschrieben)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
