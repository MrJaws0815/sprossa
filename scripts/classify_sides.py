#!/usr/bin/env python3
"""Klassifiziert die als 'beilage' markierten Rezepte feiner.

Das erste Review hat 79 Rezepte als Beilage eingestuft - darunter aber auch
leichte Hauptgerichte (Suppe, Toast, Pancakes). Hier wird entschieden:

  side       - Beilage/Dip/Sauce/Brot: allein nicht satt machend
  light_main - leichte, aber vollstaendige Mahlzeit

Ergebnis: tmp/beilagen_klassifikation.json
"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path("/home/mrjaws/monatsmenue/tmp")
REVIEW = BASE / "rezept_review.json"
DATA = BASE / "rezepte_export.json"
OUT = BASE / "beilagen_klassifikation.json"
KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines()
       if l.startswith("OPENROUTER_API_KEY=")][0]

PROMPT = """Ein deutscher Familien-Monatsplaner braucht Abendessen, die satt machen.
Ordne jedes Gericht ein:

side       = Beilage, Dip, Sauce, Brot, Salat ohne Saettigung. Allein als
             Abendessen nicht ausreichend (Rotkohl, Apfelmus, Coleslaw,
             Hummus, Bruschetta, Cornbread, Caprese).
light_main = leichte, aber vollstaendige Mahlzeit. Man wird davon satt und
             braucht nichts dazu (Suppe mit Einlage, Toast mit Belag,
             Pancakes, Fajitas, Bowl, Auflauf, Pasta).

Grenzfall-Regel: Wenn ein Gericht ueblicherweise als Beilage zu etwas
anderem serviert wird, ist es side. Wenn es typischerweise allein gegessen
wird, ist es light_main.

Antworte AUSSCHLIESSLICH als JSON-Array:
[{"titel":"<exakt>","rolle":"side|light_main","grund":"max 8 Woerter"}]
Kein Text davor oder danach.
"""


def klassifiziere(recs: list[dict]) -> list[dict]:
    block = "\n\n".join(
        f"Titel: {r['title']}\nBeschreibung: {r['description'][:200]}\nZutaten: {r['ingredients'][:300]}"
        for r in recs
    )
    body = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT + "\n\n" + block},
        ]}],
        "max_tokens": 1500,
        "temperature": 0.1,
    }
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    txt = json.load(urllib.request.urlopen(req, timeout=240))["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", txt, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return []


def main() -> int:
    review = json.loads(REVIEW.read_text())
    recipes = {r["title"]: r for r in json.loads(DATA.read_text())}
    kandidaten = [t for t, v in review.items() if v.get("komplett") == "beilage"]
    titel_liste = [review[t]["titel"] for t in kandidaten]
    print(f"{len(titel_liste)} Kandidaten", flush=True)

    recs = [recipes[t] for t in titel_liste if t in recipes]
    chunks = [recs[i:i + 10] for i in range(0, len(recs), 10)]
    ergebnis: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for chunk, antwort in zip(chunks, pool.map(klassifiziere, chunks)):
            norm = lambda s: re.sub(r"\W+", "", s.lower())
            for item in antwort:
                titel = (item.get("titel") or "").strip()
                rec = next((r for r in chunk if norm(r["title"]) == norm(titel)), None)
                if rec:
                    ergebnis[rec["id"]] = {
                        "titel": rec["title"],
                        "rolle": item.get("rolle"),
                        "grund": item.get("grund", ""),
                    }
            print(f"  {len(ergebnis)}/{len(recs)}", flush=True)

    OUT.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2), encoding="utf-8")
    from collections import Counter
    print(Counter(v["rolle"] for v in ergebnis.values()))
    print("\nSIDE:")
    for v in sorted(ergebnis.values(), key=lambda x: x["titel"]):
        if v["rolle"] == "side":
            print(f"  {v['titel'][:44]:46s} {v['grund']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
