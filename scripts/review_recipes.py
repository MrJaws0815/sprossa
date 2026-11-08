#!/usr/bin/env python3
"""Prüft alle Rezepte auf Vollständigkeit und ob sie komplette Mahlzeiten sind.

Bewertet in Batches per LLM:
  komplett   – vollständige Mahlzeit oder nur Beilage/Komponente?
  zutaten    – fehlen Mengen, Einheiten, Grundzutaten (Salz, Öl, Flüssigkeit)?
  zubereitung– Schritte, Zeiten, Temperaturen, Garhinweise ausreichend?

Ergebnis: tmp/rezept_review.json + Zusammenfassung auf stdout.
"""
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT = Path("/home/mrjaws/monatsmenue/tmp/rezept_review.json")
DATA = Path("/home/mrjaws/monatsmenue/tmp/rezepte_export.json")
KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines()
       if l.startswith("OPENROUTER_API_KEY=")][0]

PROMPT = """Du prüfst Rezepte fuer eine Familien-Ernaehrungs-App. Bewerte JEDES Rezept
streng aber fair nach drei Kriterien.

1) KOMPLETT: Ist das eine vollstaendige Mahlzeit (Hauptgericht, satt machend)?
   Oder nur eine Beilage/Komponente (z.B. Rotkohl, Sauce, Salat als Beilage,
   Brotaufstrich)? Ein Gericht, zu dem man laut allgemeinem Verstaendnis noch
   Kartoffeln/Beilage/Fleisch braucht, ist NICHT komplett.
2) ZUTATEN: Sind alle Zutaten mit Menge und Einheit vorhanden? Fehlen
   Grundzutaten, die fuer das Gelingen noetig sind (Salz, Pfeffer, Oel/Fett,
   Fluessigkeit zum Kochen, Zucker, Bindemittel)? Fehlt eine Hauptzutat?
3) ZUBEREITUNG: Sind die Schritte klar und ausfuehrbar? Fehlen Zeiten,
   Temperaturen, Garhinweise, Mengenangaben im Text, Reihenfolge?

Antworte AUSSCHLIESSLICH als JSON-Array, ein Objekt pro Rezept, in derselben
Reihenfolge wie die Eingabe:
[{"nr":1,"komplett":"ja|beilage|unklar","zutaten":"ok|maengel","zubereitung":"ok|maengel","probleme":"max 12 Woerter, konkreter Hauptmangel oder leer"}]

Kein Text davor oder danach.
"""


def export() -> list[dict]:
    sql = """
    SELECT r.id, r.title, r.description, r.instructions,
           COALESCE(string_agg(i.name || ' ' || ri.quantity || ' ' || COALESCE(ri.unit,''), '; ' ORDER BY i.name), '')
    FROM recipes r LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
    LEFT JOIN ingredients i ON i.id = ri.ingredient_id
    GROUP BY r.id, r.title, r.description, r.instructions ORDER BY r.title;
    """
    res = subprocess.run(
        ["docker", "exec", "sprossa-test-db", "psql", "-U", "sprossa", "-d", "sprossa_test",
         "-t", "-A", "-F", "\u0001", "-c", sql],
        capture_output=True, text=True,
    )
    out = []
    for line in res.stdout.strip().splitlines():
        parts = line.split("\u0001")
        if len(parts) < 5:
            continue
        rid, title, desc, instr, ings = parts[:5]
        out.append({"id": rid, "title": title, "description": desc or "",
                    "instructions": instr or "", "ingredients": ings})
    return out


def batch_block(recipes: list[dict], start: int) -> str:
    teile = []
    for i, r in enumerate(recipes, start):
        teile.append(
            f"--- Rezept {i} ---\nTitel: {r['title']}\n"
            f"Zutaten: {r['ingredients']}\nZubereitung: {r['instructions']}"
        )
    return "\n\n".join(teile)


def review_chunk(args):
    chunk, start = args
    import urllib.request
    body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": PROMPT + "\n\n" + batch_block(chunk, start)}]}],
        "max_tokens": 2500, "temperature": 0.1}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    txt = json.load(urllib.request.urlopen(req, timeout=300))["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", txt, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return []


def main() -> int:
    recipes = export()
    print(f"{len(recipes)} Rezepte exportiert", flush=True)
    DATA.write_text(json.dumps(recipes, ensure_ascii=False, indent=2), encoding="utf-8")

    chunks = []
    size = 8
    for i in range(0, len(recipes), size):
        chunks.append((recipes[i:i + size], i + 1))

    results: dict[str, dict] = json.loads(OUT.read_text()) if OUT.exists() else {}
    print(f"bereits bewertet: {len(results)}", flush=True)

    # Chunks ueberspringen, deren Rezepte schon bewertet sind
    chunks = [c for c in chunks if any(r["id"] not in results for r in c[0])]

    with ThreadPoolExecutor(max_workers=4) as pool:
        for (chunk, start), antwort in zip(chunks, pool.map(review_chunk, chunks)):
            for item in antwort:
                nr = item.get("nr")
                if not isinstance(nr, int) or not (start <= nr <= start + len(chunk) - 1):
                    continue
                rec = chunk[nr - start]
                results[rec["id"]] = {
                    "titel": rec["title"],
                    **{k: item.get(k) for k in ("komplett", "zutaten", "zubereitung", "probleme")},
                }
            print(f"  {len(results)}/{len(recipes)}", flush=True)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    print("\n=== KOMPLETT ===")
    print(dict(Counter(r.get("komplett") for r in results.values())))
    print("=== ZUTATEN ===")
    print(dict(Counter(r.get("zutaten") for r in results.values())))
    print("=== ZUBEREITUNG ===")
    print(dict(Counter(r.get("zubereitung") for r in results.values())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
