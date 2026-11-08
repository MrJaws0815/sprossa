#!/usr/bin/env python3
"""Legt 'Wasser' als Zutat an und traegt es dort ein, wo es im Text steht.

Nach dem Umbau der Zubereitungen nennen viele Rezepte Wassermengen
("200 ml Wasser"), die Zutatenliste kannte Wasser aber nicht - ein Bruch
zwischen Text und Einkaufsliste.

Mengen werden aus dem Text gelesen. Wo keine Zahl steht ("Wasser nach
Bedarf"), wird 250 ml als Hausnummer eingetragen und der Eintrag als
optional markiert.

    python3 scripts/add_water_ingredient.py [--dry-run]
"""
import argparse
import re
import subprocess
import uuid

DB = "sprossa-test-db"

# "200 ml Wasser", "1 Liter Wasser", "250 ml lauwarmes Wasser"
MENGE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(ml|milliliter|l|liter|tassen?)\s+"
    r"(?:[\wäöüß]+\s+){0,2}?wasser",
    re.IGNORECASE,
)
EINHEIT = {"ml": "ml", "milliliter": "ml", "l": "l", "liter": "l",
           "tasse": "Tasse", "tassen": "Tasse"}


def psql(sql: str) -> str:
    res = subprocess.run(
        ["docker", "exec", "-i", DB, "psql", "-U", "sprossa", "-d", "sprossa_test",
         "-v", "ON_ERROR_STOP=1", "-t", "-A", "-F", "\t"],
        input=sql, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(res.stderr[:400])
    return res.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Zutat anlegen, falls sie fehlt
    vorhanden = psql("SELECT id FROM ingredients WHERE lower(name)='wasser';")
    if vorhanden:
        wasser_id = vorhanden.splitlines()[0]
        print(f"Zutat 'Wasser' existiert: {wasser_id}")
    else:
        wasser_id = str(uuid.uuid4())
        print("Zutat 'Wasser' wird angelegt")

    # Als JSON exportieren: Zeilenumbrüche in instructions zerlegen sonst die
    # Textausgabe (derselbe Fallstrick wie beim ersten Rezept-Export).
    import json as _json
    rows = _json.loads(psql("""
        SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) FROM (
            SELECT r.id, r.title, r.instructions,
                   COALESCE((SELECT string_agg(i.name, ' | ')
                             FROM recipe_ingredients ri JOIN ingredients i ON i.id = ri.ingredient_id
                             WHERE ri.recipe_id = r.id), '') AS zutaten
            FROM recipes r
            WHERE r.instructions ~* 'wasser'
        ) t;
    """))

    sql = ["BEGIN;"]
    if not vorhanden:
        sql.append(
            f"INSERT INTO ingredients (id, name, category, unit_default) "
            f"VALUES ('{wasser_id}', 'Wasser', 'Vorrat & Konserven', 'ml');"
        )

    eintraege, ohne_menge = 0, 0
    details = []
    for rec in rows:
        rid, title, instr = rec["id"], rec["title"], rec["instructions"] or ""
        zutaten = rec["zutaten"] or ""
        if "wasser" in zutaten.lower():
            continue  # steht schon in der Zutatenliste

        treffer = MENGE_RE.findall(instr)
        if treffer:
            menge_txt, einheit_txt = treffer[0]
            menge = float(menge_txt.replace(",", "."))
            einheit = EINHEIT.get(einheit_txt.lower(), "ml")
            optional = "false"
        else:
            # Keine Zahl im Text ("Wasser nach Bedarf", "in Salzwasser kochen"):
            # Dann keine Zutat erfinden - eine Hausnummer waere hier falsch.
            ohne_menge += 1
            continue

        sql.append(
            f"INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, "
            f"is_optional, pre_processed) VALUES ('{uuid.uuid4()}', '{rid}', '{wasser_id}', "
            f"{menge}, '{einheit}', {optional}, false);"
        )
        eintraege += 1
        details.append((title, f"{menge:g} {einheit}", optional == "true"))
    sql.append("COMMIT;")

    print(f"{eintraege} Rezepte bekommen Wasser ({ohne_menge} ohne Mengenangabe im Text)")
    for t, m, opt in details[:10]:
        print(f"  {t[:44]:46s} {m}{'  (optional)' if opt else ''}")

    if args.dry_run:
        print("dry-run, nichts geschrieben")
        return 0

    psql("\n".join(sql))
    print("geschrieben.")
    print("Rezepte ohne Wasser, obwohl im Text genannt:",
          psql("""
            SELECT count(*) FROM recipes r
            WHERE r.instructions ~* 'wasser'
              AND NOT EXISTS (SELECT 1 FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id
                              WHERE ri.recipe_id=r.id AND lower(i.name)='wasser');
          """))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
