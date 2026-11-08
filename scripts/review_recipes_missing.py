#!/usr/bin/env python3
"""Bewertet die noch fehlenden Rezepte (Rest aus scripts/review_recipes.py).

Zuordnung ueber den Titel statt ueber Nummern - Nummern sind bei
verschobenen Chunks zu fehleranfaellig.
"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path("/home/mrjaws/monatsmenue/tmp")
OUT = BASE / "rezept_review.json"
DATA = BASE / "rezepte_export.json"
KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines()
       if l.startswith("OPENROUTER_API_KEY=")][0]

PROMPT = """Du pruefst Rezepte fuer eine Familien-Ernaehrungs-App. Bewerte JEDES
Rezept streng aber fair.

1) KOMPLETT: vollstaendige Mahlzeit (Hauptgericht, satt machend) oder nur
   Beilage/Komponente (Rotkohl, Dip, Salat als Beilage, Brotaufstrich)?
2) ZUTATEN: alle Zutaten mit Menge und Einheit? Fehlen Grundzutaten
   (Salz, Pfeffer, Oel/Fett, Fluessigkeit, Zucker, Bindemittel) oder eine
   Hauptzutat?
3) ZUBEREITUNG: Schritte klar ausfuehrbar? Fehlen Zeiten, Temperaturen,
   Garhinweise?

Antworte AUSSCHLIESSLICH als JSON-Array, ein Objekt pro Rezept:
[{"titel":"<exakt der Titel aus der Eingabe>","komplett":"ja|beilage|unklar","zutaten":"ok|maengel","zubereitung":"ok|maengel","probleme":"max 12 Woerter"}]
Kein Text davor oder danach.
"""


def chunk_text(recs: list[dict]) -> str:
    return "\n\n".join(
        f"--- Rezept ---\nTitel: {r['title']}\nZutaten: {r['ingredients']}\nZubereitung: {r['instructions']}"
        for r in recs
    )


def review(recs: list[dict]) -> list[dict]:
    body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": PROMPT + "\n\n" + chunk_text(recs)}]}],
        "max_tokens": 2000, "temperature": 0.1}
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
    all_recipes = json.loads(DATA.read_text())
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    fehlend = [r for r in all_recipes if r["id"] not in results]
    print(f"{len(all_recipes)} gesamt, {len(fehlend)} offen", flush=True)

    chunks = [fehlend[i:i + 8] for i in range(0, len(fehlend), 8)]
    print(f"{len(chunks)} Chunks", flush=True)

    fertig = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for chunk, antwort in zip(chunks, pool.map(review, chunks)):
            by_title = {r["title"]: r for r in chunk}
            for item in antwort:
                title = (item.get("titel") or "").strip()
                rec = by_title.get(title)
                if rec is None:
                    # toleranter Vergleich (Whitespace, Sonderzeichen)
                    norm = lambda s: re.sub(r"\W+", "", s.lower())
                    rec = next((r for t, r in by_title.items() if norm(t) == norm(title)), None)
                if rec is None:
                    continue
                results[rec["id"]] = {
                    "titel": rec["title"],
                    **{k: item.get(k) for k in ("komplett", "zutaten", "zubereitung", "probleme")},
                }
            fertig += len(chunk)
            print(f"  {len(results)}/{len(all_recipes)}", flush=True)
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    print("\n=== KOMPLETT ===", dict(Counter(v.get("komplett") for v in results.values())))
    print("=== ZUTATEN ===", dict(Counter(v.get("zutaten") for v in results.values())))
    print("=== ZUBEREITUNG ===", dict(Counter(v.get("zubereitung") for v in results.values())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
