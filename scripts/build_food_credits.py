"""Erzeugt frontend/lib/food-credits.ts für die Bildnachweis-Seite.

Nur Bilder, die tatsächlich im Bestand sind (Status ok, Note <=3, Datei da).
"""
import json
from pathlib import Path

RES = Path("/home/mrjaws/monatsmenue/tmp/food_batch_results.json")
CRED = Path("/home/mrjaws/monatsmenue/tmp/food_credits.json")
FOOD = Path("/home/mrjaws/monatsmenue/frontend/public/food")
OUT = Path("/home/mrjaws/monatsmenue/frontend/lib/food-credits.ts")

results = json.loads(RES.read_text())
credits = json.loads(CRED.read_text())

eintraege = []
for slug, v in sorted(results.items(), key=lambda kv: kv[1].get("rezept", "")):
    if v.get("status") != "ok" or (v.get("note") or 9) > 3:
        continue
    if not (FOOD / f"{slug}.webp").exists():
        continue
    c = credits.get(slug, {})
    eintraege.append({
        "rezept": v.get("rezept") or slug,
        "foto": c.get("creator") or "Urheber nicht angegeben",
        "lizenz": (c.get("license") or "unbekannt").upper(),
        "version": c.get("license_version") or "",
        "quelle": c.get("source") or "",
        "url": c.get("foreign_landing_url") or "",
    })

lines = [
    "// Automatisch erzeugt von scripts/build_food_credits.py — nicht von Hand editieren.",
    "// Grundlage: CC-BY/BY-SA verlangen eine sichtbare Namensnennung.",
    "",
    "export type FoodCredit = {",
    "  rezept: string;",
    "  foto: string;",
    "  lizenz: string;",
    "  version: string;",
    "  quelle: string;",
    "  url: string;",
    "};",
    "",
    f"export const FOOD_CREDITS: FoodCredit[] = {json.dumps(eintraege, ensure_ascii=False, indent=2)};",
    "",
]
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"{len(eintraege)} Eintraege → {OUT}")
print(f"Datei: {OUT.stat().st_size // 1024} KB")
