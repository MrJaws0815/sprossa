#!/usr/bin/env python3
"""Ueberarbeitet Rezept-Zubereitungen: klare Schritte, Zeiten, Temperaturen.

Das Review fand bei 248 von 314 Rezepten Maengel: fehlende Temperaturen,
fehlende Garzeiten, unklare Reihenfolge.

Regeln fuer den Umbau (bewusst konservativ):
  - Keine Zutaten erfinden, keine Mengen aendern.
  - Fehlende Zeiten/Temperaturen nur ergaenzen, wenn sie sich aus dem Gericht
    zwingend ergeben (Standardgarzeiten). Sonst Formulierung praezisieren.
  - Schritte einzeln, mit Nummer, je ein Arbeitsschritt.
  - Ergebnis ersetzen, Originale liegen in recipes_instructions_backup.

    python3 scripts/rewrite_instructions.py --limit 5   # Probelauf
    python3 scripts/rewrite_instructions.py
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path("/home/mrjaws/monatsmenue/tmp")
OUT = BASE / "instructions_rewrite.json"
DB = "sprossa-test-db"
KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines()
       if l.startswith("OPENROUTER_API_KEY=")][0]

PROMPT = """Ueberarbeite die Zubereitung eines Rezepts fuer eine Familien-App, damit
sie eindeutig nachkochbar ist.

HARTE REGELN:
- Erfinde KEINE Zutaten und aendere KEINE Mengen.
- Ergänze eine Zeit oder Temperatur nur, wenn sie sich aus dem Gericht
  zwingend ergibt (z.B. "bei 180 °C ca. 25 Minuten garen" fuer einen Auflauf).
  Im Zweifel formuliere lieber praeziser statt zu raten.
- Jeder Schritt eine Taetigkeit, nummeriert mit "1. ", "2. " ...
- Nenne Gargrad/Hinweise, wo sie helfen (goldbraun, bissfest, saemig).
- Sprache: Deutsch, Du-Form vermeiden, neutral ("die Zwiebeln wuerfeln").
- Laenge: 4-8 Schritte, kein Roman.

Gib NUR den neuen Zubereitungstext zurueck, ohne Einleitung, ohne Titel.
"""


def psql(sql: str) -> str:
    res = subprocess.run(["docker", "exec", "-i", DB, "psql", "-U", "sprossa", "-d", "sprossa_test",
                          "-v", "ON_ERROR_STOP=1", "-t", "-A", "-c", sql],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(res.stderr[:400])
    return res.stdout.strip()


def rewrite(rec: dict) -> tuple[str, str | None]:
    body = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT +
             f"\n\nRezept: {rec['title']}\nZutaten: {rec['ingredients']}\n\n"
             f"Bisherige Zubereitung:\n{rec['instructions']}"},
        ]}],
        "max_tokens": 900,
        "temperature": 0.2,
    }
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        txt = json.load(urllib.request.urlopen(req, timeout=240))["choices"][0]["message"]["content"]
    except Exception:
        return rec["id"], None
    txt = (txt or "").strip()
    if len(txt) < 80:
        return rec["id"], None
    return rec["id"], txt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rows = psql("""
        SELECT json_agg(row_to_json(t)) FROM (
          SELECT r.id, r.title, COALESCE(r.instructions,'') AS instructions,
                 COALESCE(string_agg(i.name || ' ' || ri.quantity || ' ' || COALESCE(ri.unit,''), '; ' ORDER BY i.name), '') AS ingredients
          FROM recipes r LEFT JOIN recipe_ingredients ri ON ri.recipe_id=r.id
          LEFT JOIN ingredients i ON i.id=ri.ingredient_id
          GROUP BY r.id, r.title, r.instructions ORDER BY r.title
        ) t;
    """)
    recipes = json.loads(rows)
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [r for r in recipes if r["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(recipes)} Rezepte, {len(todo)} offen", flush=True)

    ok = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rid, txt in pool.map(rewrite, todo):
            if txt:
                done[rid] = txt
                ok += 1
            if len(done) % 20 == 0:
                OUT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  {len(done)} geschrieben", flush=True)

    OUT.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{ok} neu ueberarbeitet, {len(done)} insgesamt")

    if args.limit:
        print("\n--- Probelauf, nichts in die DB geschrieben ---")
        for rid, txt in list(done.items())[:3]:
            print(f"\n### {rid}\n{txt[:600]}")
        return 0

    # In die DB schreiben (Originale stehen in recipes_instructions_backup)
    sql = ["BEGIN;"]
    for rid, txt in done.items():
        safe = txt.replace("'", "''")
        sql.append(f"UPDATE recipes SET instructions = '{safe}' WHERE id = '{rid}';")
    sql.append("COMMIT;")
    psql("\n".join(sql))
    print("in die Datenbank geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
