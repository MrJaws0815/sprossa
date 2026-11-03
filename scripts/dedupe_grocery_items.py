#!/usr/bin/env python3
"""Bereinigt Legacy-Mehrfachzeilen in Einkaufslisten (Task 80).

WICHTIG: Vorher ein Backup der Datenbank erstellen (scripts/backup_db.sh)!

Gruppiert grocery_items nach (grocery_list_id, _group_key, unit):
- Summiert quantity_total
- Behaelt eine Zeile, loescht Duplikate

Default: DRY-RUN (zeigt nur an, was passieren wuerde).
Mit --apply: fuehrt die Aenderungen aus.
Idempotent: Ein zweiter Lauf aendert nichts mehr.
"""
import argparse
import asyncio
import os
import sys

# Backend-Verzeichnis zum PYTHONPATH hinzufuegen
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models.database import GroceryItem
from app.services.grocery_engine import _group_key


async def dedupe_grocery_items(apply: bool = False):
    async with async_session_factory() as session:
        stmt = select(GroceryItem).options(selectinload(GroceryItem.ingredient))
        result = await session.execute(stmt)
        items = result.scalars().all()

        groups = defaultdict(list)
        for item in items:
            ing = item.ingredient
            name = ing.name if ing else ""
            category = ing.category if ing else None
            key = _group_key(name, category)
            groups[(item.grocery_list_id, key, item.unit)].append(item)

        merged_count = 0
        deleted_count = 0
        affected_groups = 0

        for group_key, group_items in groups.items():
            if len(group_items) <= 1:
                continue

            affected_groups += 1
            total_qty = sum(it.quantity_total for it in group_items)
            keep = group_items[0]
            to_delete = group_items[1:]

            print(
                f"[{'APPLY' if apply else 'DRY-RUN'}] Liste {group_key[0]} | "
                f"Gruppe '{group_key[1]}' | Einheit {group_key[2]} | "
                f"{len(group_items)} Zeilen -> 1 Zeile | "
                f"Menge {sum(it.quantity_total for it in group_items)} -> {total_qty}"
            )

            if apply:
                keep.quantity_total = total_qty
                for it in to_delete:
                    await session.delete(it)
                merged_count += 1
                deleted_count += len(to_delete)

        if apply:
            await session.commit()
            print(f"\nFertig: {merged_count} Gruppen zusammengefuehrt, {deleted_count} Zeilen geloescht.")
        else:
            print(f"\nDry-Run: {affected_groups} Gruppen betroffen. Keine Aenderungen vorgenommen.")


def main():
    parser = argparse.ArgumentParser(description="Legacy-Mehrfachzeilen in Einkaufslisten bereinigen.")
    parser.add_argument("--apply", action="store_true", help="Aenderungen tatsaechlich ausfuehren (Default: Dry-Run).")
    args = parser.parse_args()

    asyncio.run(dedupe_grocery_items(apply=args.apply))


if __name__ == "__main__":
    main()
