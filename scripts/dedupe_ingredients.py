#!/usr/bin/env python3
"""Sprossa – Dedupe suffix ingredients (e.g. Kartoffeln_1361fc -> Kartoffeln).

Problem:
    Seed-Import created duplicate ingredients with _[0-9a-f]{6} suffix instead of
    reusing existing base ingredients. Result: 26 duplicate ingredients, 44
    recipe_ingredients and 81 grocery_items referencing them. The shopping list
    shows e.g. "Kartoffeln" AND "Kartoffeln_1361fc" as separate items.

Fix:
    1. Find ingredients whose name matches _[0-9a-f]{6}$.
    2. Extract base name (regexp_replace).
    3. If base ingredient exists:
       - Re-point recipe_ingredients.ingredient_id and grocery_items.ingredient_id to base.
       - Merge conflicts:
         * recipe_ingredients: if (recipe_id, ingredient_id) duplicates -> sum quantities,
           delete duplicate row.
         * grocery_items: if (grocery_list_id, ingredient_id) duplicates -> sum quantity_total,
           is_checked = AND of both, delete duplicate row.
       - Delete suffix ingredient.
    4. If base ingredient does NOT exist:
       - Rename suffix ingredient to base name (strip suffix). No merge needed.

Usage:
    python3 scripts/dedupe_ingredients.py --dry-run   # default
    python3 scripts/dedupe_ingredients.py --apply
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    os.environ.get(
        "MM_DATABASE_URL_SYNC",
        "postgresql://sprossa:sprossa@localhost:5433/sprossa_test",
    ),
)

SUFFIX_RE = re.compile(r"_[0-9a-f]{6}$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Änderungen schreiben")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen (Default)")
    args = ap.parse_args()
    apply = args.apply

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, category, unit_default FROM ingredients "
                "WHERE name ~ '_[0-9a-f]{6}$' ORDER BY name;"
            )
            suffix_ingredients = cur.fetchall()

            total_merged = 0
            total_renamed = 0
            total_ri_updated = 0
            total_gi_updated = 0
            total_ri_deleted = 0
            total_gi_deleted = 0

            for suffix_id, suffix_name, suffix_category, suffix_unit in suffix_ingredients:
                base_name = SUFFIX_RE.sub("", suffix_name)

                cur.execute("SELECT id, name FROM ingredients WHERE name = %s;", (base_name,))
                base_row = cur.fetchone()

                if base_row:
                    base_id = base_row[0]
                    if not apply:
                        cur.execute(
                            "SELECT count(*) FROM recipe_ingredients WHERE ingredient_id = %s;",
                            (suffix_id,),
                        )
                        ri_count = cur.fetchone()[0]
                        cur.execute(
                            "SELECT count(*) FROM grocery_items WHERE ingredient_id = %s;",
                            (suffix_id,),
                        )
                        gi_count = cur.fetchone()[0]
                        print(
                            f"  [dry-run] '{suffix_name}' ({suffix_category}) "
                            f"-> merge into '{base_name}' [{base_id}]: "
                            f"{ri_count} recipe_ingredients, {gi_count} grocery_items"
                        )
                        total_merged += 1
                        continue

                    # --- 1. Update FKs in recipe_ingredients ---
                    cur.execute(
                        "UPDATE recipe_ingredients SET ingredient_id = %s WHERE ingredient_id = %s;",
                        (base_id, suffix_id),
                    )
                    total_ri_updated += cur.rowcount

                    # --- 2. Update FKs in grocery_items ---
                    cur.execute(
                        "UPDATE grocery_items SET ingredient_id = %s WHERE ingredient_id = %s;",
                        (base_id, suffix_id),
                    )
                    total_gi_updated += cur.rowcount

                    # --- 3. Merge duplicate recipe_ingredients ---
                    # Sum quantities into the row with the lowest id per
                    # (recipe_id, ingredient_id, unit). Units are part of the key:
                    # adding 200 g + 2 Stück would be nonsense, so different-unit
                    # rows stay separate (both now point to the base ingredient).
                    cur.execute(
                        """
                        WITH duplicates AS (
                            SELECT recipe_id, ingredient_id, unit,
                                   MIN(id::text)::uuid AS keep_id,
                                   SUM(quantity) AS total_qty
                              FROM recipe_ingredients
                             WHERE ingredient_id = %s
                             GROUP BY recipe_id, ingredient_id, unit
                            HAVING COUNT(*) > 1
                        )
                        UPDATE recipe_ingredients
                           SET quantity = duplicates.total_qty
                          FROM duplicates
                         WHERE recipe_ingredients.id = duplicates.keep_id;
                        """,
                        (base_id,),
                    )
                    cur.execute(
                        """
                        DELETE FROM recipe_ingredients
                         WHERE ingredient_id = %s
                           AND id NOT IN (
                               SELECT MIN(id::text)::uuid
                                 FROM recipe_ingredients
                                WHERE ingredient_id = %s
                                GROUP BY recipe_id, unit
                           );
                        """,
                        (base_id, base_id),
                    )
                    total_ri_deleted += cur.rowcount

                    # --- 4. Merge duplicate grocery_items ---
                    # Sum quantity_total, AND is_checked into the row with the lowest
                    # id per (grocery_list_id, ingredient_id, unit). Mixed units stay
                    # separate for the same reason as above.
                    cur.execute(
                        """
                        WITH duplicates AS (
                            SELECT grocery_list_id, ingredient_id, unit,
                                   MIN(id::text)::uuid AS keep_id,
                                   SUM(quantity_total) AS total_qty,
                                   bool_and(is_checked) AS and_checked
                              FROM grocery_items
                             WHERE ingredient_id = %s
                             GROUP BY grocery_list_id, ingredient_id, unit
                            HAVING COUNT(*) > 1
                        )
                        UPDATE grocery_items
                           SET quantity_total = duplicates.total_qty,
                               is_checked = duplicates.and_checked
                          FROM duplicates
                         WHERE grocery_items.id = duplicates.keep_id;
                        """,
                        (base_id,),
                    )
                    cur.execute(
                        """
                        DELETE FROM grocery_items
                         WHERE ingredient_id = %s
                           AND id NOT IN (
                               SELECT MIN(id::text)::uuid
                                 FROM grocery_items
                                WHERE ingredient_id = %s
                                GROUP BY grocery_list_id, unit
                           );
                        """,
                        (base_id, base_id),
                    )
                    total_gi_deleted += cur.rowcount

                    # --- 5. Delete the suffix ingredient ---
                    cur.execute("DELETE FROM ingredients WHERE id = %s;", (suffix_id,))
                    total_merged += 1

                else:
                    # --- Base does NOT exist: rename the suffix ingredient ---
                    if not apply:
                        print(f"  [dry-run] '{suffix_name}' -> rename to '{base_name}' (no base exists).")
                        total_renamed += 1
                        continue

                    cur.execute(
                        "UPDATE ingredients SET name = %s WHERE id = %s;",
                        (base_name, suffix_id),
                    )
                    total_renamed += 1

            if apply:
                conn.commit()
                print(
                    f"\n✅ Änderungen committet. "
                    f"Gemerged: {total_merged}, umbenannt: {total_renamed}."
                )
                print(
                    f"   recipe_ingredients: {total_ri_updated} aktualisiert, "
                    f"{total_ri_deleted} Duplikat-Zeilen gelöscht."
                )
                print(
                    f"   grocery_items: {total_gi_updated} aktualisiert, "
                    f"{total_gi_deleted} Duplikat-Zeilen gelöscht."
                )
            else:
                conn.rollback()
                print(
                    f"\n(dry-run) Würde {total_merged} Ingredients mergen, "
                    f"{total_renamed} umbenennen. Keine Änderungen geschrieben."
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
