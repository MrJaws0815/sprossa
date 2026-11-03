#!/usr/bin/env python3
"""Sprossa – Kategorie-Normalisierung (Task 53).

Mappt die historisch gewachsenen, gemischt deutsch/englischen Zutaten- und
Einkaufslisten-Kategorien auf einen kanonischen Satz, der exakt der
Supermarkt-Gang-Reihenfolge entspricht.

Nutzt `docker exec psql` gegen den Test-Container – keine Python-DB-Treiber
nötig.

Nutzung:
    python3 scripts/normalize_categories.py --dry-run
    python3 scripts/normalize_categories.py --apply
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from collections import Counter

CONTAINER = "sprossa-test-db"
DB_USER = "sprossa"
DB_NAME = "sprossa_test"

CANONICAL: list[str] = [
    "Gemüse",
    "Obst",
    "Fleisch",
    "Fisch",
    "Milchprodukte & Eier",
    "Backwaren",
    "Tiefkühl",
    "Getränke",
    "Vorrat & Konserven",
    "Gewürze",
    "Sonstiges",
]

MAPPING: dict[str, str] = {
    # Gemüse
    "gemüse": "Gemüse", "gemuese": "Gemüse", "vegetables": "Gemüse",
    "gemüse & kräuter": "Gemüse", "kräuter": "Gemüse", "algen": "Gemüse",
    # Obst
    "obst": "Obst", "fruit": "Obst", "fruits": "Obst", "beeren": "Obst",
    # Fleisch
    "fleisch": "Fleisch", "meat": "Fleisch", "geflügel": "Fleisch",
    "wurst": "Fleisch", "fleisch & fisch": "Fleisch",
    # Fisch
    "fisch": "Fisch", "fish": "Fisch", "meeresfrüchte": "Fisch",
    "fisch & meeresfrüchte": "Fisch", "seafood": "Fisch",
    # Milchprodukte & Eier
    "milchprodukte": "Milchprodukte & Eier", "dairy": "Milchprodukte & Eier",
    "dairy & eggs": "Milchprodukte & Eier", "eier": "Milchprodukte & Eier",
    "eggs": "Milchprodukte & Eier", "käse": "Milchprodukte & Eier",
    # Backwaren
    "backwaren": "Backwaren", "bread": "Backwaren", "bakery": "Backwaren",
    "backzutaten": "Backwaren", "baking": "Backwaren",
    # Tiefkühl
    "tiefkühl": "Tiefkühl", "tiefkuehl": "Tiefkühl", "frozen": "Tiefkühl",
    "tk & fertigprodukte": "Tiefkühl",
    # Getränke
    "getränke": "Getränke", "getraenke": "Getränke", "beverages": "Getränke",
    "drinks": "Getränke",
    # Vorrat & Konserven
    "vorrat": "Vorrat & Konserven", "konserven": "Vorrat & Konserven",
    "canned": "Vorrat & Konserven", "condiments": "Vorrat & Konserven",
    "pantry": "Vorrat & Konserven", "getreide": "Vorrat & Konserven",
    "grains": "Vorrat & Konserven", "reis & getreide": "Vorrat & Konserven",
    "nudeln": "Vorrat & Konserven", "hülsenfrüchte": "Vorrat & Konserven",
    "nüsse": "Vorrat & Konserven", "soßen & öle": "Vorrat & Konserven",
    "soßen & oele": "Vorrat & Konserven", "sauces": "Vorrat & Konserven",
    "oils": "Vorrat & Konserven",
    # Gewürze
    "gewürze": "Gewürze", "gewuerze": "Gewürze", "spices": "Gewürze",
    "gewürze & brühen": "Gewürze", "brühen": "Gewürze",
    # Sonstiges
    "other": "Sonstiges", "sonstiges": "Sonstiges", "misc": "Sonstiges",
    "küchenbedarf": "Sonstiges", "kuechenbedarf": "Sonstiges",
    "hilfsmittel": "Sonstiges", "tofu": "Sonstiges",
}


def canonical(raw: str | None) -> str:
    if not raw:
        return "Sonstiges"
    return MAPPING.get(str(raw).strip().lower(), "Sonstiges")


def psql(sql: str, tuples_only: bool = False) -> str:
    args = ["docker", "exec", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME]
    if tuples_only:
        args += ["-t", "-A", "-F", "\t"]
    args += ["-c", sql]
    res = subprocess.run(args, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"psql failed: {res.stderr.strip()}")
    return res.stdout


def esc(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("--apply oder --dry-run angeben")

    rows = []
    for line in psql(
        "SELECT category, count(*) FROM ingredients GROUP BY 1 ORDER BY 2 DESC;",
        tuples_only=True,
    ).splitlines():
        if not line.strip():
            continue
        cat, n = line.rsplit("\t", 1)
        rows.append((cat, int(n)))

    print("=== ingredients.category (Ist → Soll) ===")
    changes: Counter[str] = Counter()
    for cat, n in rows:
        target = canonical(cat)
        changes[target] += n
        flag = "" if cat == target else "  ←"
        print(f"  {cat:28s} {n:5d} → {target}{flag}")

    print("\n=== Zielverteilung ===")
    for target in CANONICAL:
        if changes[target]:
            print(f"  {target:24s} {changes[target]:5d}")

    unknown = [c for c, _ in rows if canonical(c) == "Sonstiges" and c.lower() not in MAPPING]
    if unknown:
        print("\n⚠️  Unbekannte Kategorien (landen in Sonstiges):", ", ".join(unknown))

    if args.apply:
        stmts = []
        for cat, _ in rows:
            target = canonical(cat)
            if cat != target:
                stmts.append(
                    f"UPDATE ingredients SET category = {esc(target)} WHERE category = {esc(cat)};"
                )
        for line in psql(
            "SELECT DISTINCT category_override FROM grocery_items WHERE category_override IS NOT NULL;",
            tuples_only=True,
        ).splitlines():
            if not line.strip():
                continue
            target = canonical(line)
            if line != target:
                stmts.append(
                    f"UPDATE grocery_items SET category_override = {esc(target)} WHERE category_override = {esc(line)};"
                )
        if not stmts:
            print("\nNichts zu tun – alle Kategorien bereits kanonisch.")
            return 0
        out = psql("\n".join(stmts))
        print("\n" + out.strip())
        print(f"✅ APPLIED: {len(stmts)} UPDATE-Statements ausgeführt.")
    else:
        print("\n(dry-run – keine Änderungen geschrieben)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
