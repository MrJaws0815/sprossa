#!/usr/bin/env python3
"""Ergänzt fehlende Grundzutaten (Salz, Pfeffer, Öl) in den Rezepten.

Das Review fand: Salz fehlt in 197, Pfeffer in 148, Öl in 63 Rezepten.
Ohne diese Angaben ist ein Rezept nicht vollständig nachkochbar - und die
Einkaufsliste suggeriert, man brauche kein Salz.

Regelbasiert, damit deterministisch:
  - fehlt Salz    -> 1 Prise
  - fehlt Pfeffer -> 1 Prise
  - fehlt Öl/Fett -> 2 EL Olivenöl (mediterran) bzw. Rapsöl (asiatisch)

Bereits vorhandene Zutaten (auch als "Salz und Pfeffer") werden erkannt und
nicht doppelt eingefügt.

    python3 scripts/add_missing_ingredients.py [--dry-run]
"""
import argparse
import re
import subprocess
import uuid
from pathlib import Path

DB = "sprossa-test-db"

# Was gilt als vorhanden? (Teiltreffer, klein geschrieben)
VORHANDEN = {
    "salz": ("salz",),
    "pfeffer": ("pfeffer",),
    "oel": ("öl", "oel", "butter", "fett", "schmalz", "margarine"),
}

ASIATISCH = ("asia", "china", "chines", "japan", "thai", "vietnam", "indones",
             "wok", "curry", "korea", "sushi", "ramen", "bangkok")


def psql(sql: str) -> str:
    res = subprocess.run(["docker", "exec", "-i", DB, "psql", "-U", "sprossa",
                          "-d", "sprossa_test", "-v", "ON_ERROR_STOP=1",
                          "-t", "-A", "-F", "\t"],
                         input=sql, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(res.stderr[:400])
    return res.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Rezepte mit ihren Zutatennamen
    rows = psql("""
        SELECT r.id, r.title,
               COALESCE(string_agg(i.name, ' | '), '')
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
        LEFT JOIN ingredients i ON i.id = ri.ingredient_id
        GROUP BY r.id, r.title;
    """).splitlines()

    ids = {}
    for line in psql("SELECT id, name FROM ingredients WHERE lower(name) IN "
                     "('salz','pfeffer','olivenöl','rapsöl');").splitlines():
        gid, name = line.split("\t")
        ids[name.lower()] = gid
    fehlend_ids = {"salz", "pfeffer", "olivenöl", "rapsöl"} - set(ids)
    if fehlend_ids:
        raise SystemExit(f"Zutaten fehlen in der DB: {fehlend_ids}")

    sql = ["BEGIN;"]
    geaendert = 0
    details = []
    for line in rows:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rid, title, ing_str = parts[0], parts[1], parts[2].lower()
        vorhanden = set(ing_str.split(" | ")) if ing_str else set()
        flach = " ".join(vorhanden)

        neu = []
        if not any(x in flach for x in VORHANDEN["salz"]):
            neu.append(("salz", 1.0, "Prise"))
        if not any(x in flach for x in VORHANDEN["pfeffer"]):
            neu.append(("pfeffer", 1.0, "Prise"))
        if not any(x in flach for x in VORHANDEN["oel"]):
            oel = "rapsöl" if any(k in title.lower() for k in ASIATISCH) else "olivenöl"
            neu.append((oel, 2.0, "EL"))

        for name, qty, unit in neu:
            sql.append(
                f"INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, "
                f"is_optional, pre_processed) "
                f"VALUES ('{uuid.uuid4()}', '{rid}', '{ids[name]}', {qty}, '{unit}', false, false);"
            )
            geaendert += 1
        if neu:
            details.append((title, [n for n, _, _ in neu]))

    sql.append("COMMIT;")
    print(f"{len(details)} Rezepte bekommen Zutaten, {geaendert} Einträge")

    if args.dry_run:
        for t, n in details[:15]:
            print(f"  {t[:44]:46s} + {', '.join(n)}")
        print("  ... (dry-run, nichts geschrieben)")
        return 0

    psql("\n".join(sql))
    print("geschrieben.")

    # Kontrolle
    rest = psql("""
        SELECT count(*) FROM recipes r
        WHERE NOT EXISTS (SELECT 1 FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id
                          WHERE ri.recipe_id=r.id AND lower(i.name)='salz');
    """)
    print("Rezepte ohne Salz (danach):", rest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
