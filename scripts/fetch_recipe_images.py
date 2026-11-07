"""Prototyp: lizenzfreie Rezeptbilder über Openverse holen.

Nur kommerziell nutzbare Lizenzen (CC0, CC-BY, CC-BY-SA). CC-BY verlangt
Namensnennung, deshalb wird der Urheber mitgespeichert.

Ergebnis:
  frontend/public/food/<slug>.webp   – Bild, 1200 px breit
  tmp/food_credits.json              – Lizenz + Urheber + Quell-URL je Bild
"""
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

OUT = Path("/home/mrjaws/monatsmenue/frontend/public/food")
OUT.mkdir(parents=True, exist_ok=True)
CREDITS = Path("/home/mrjaws/monatsmenue/tmp/food_credits.json")

API = "https://api.openverse.org/v1/images/"
UA = "Sprossa/1.0 (Rezeptbilder; kontakt@sprossa.de)"

# slug -> (deutscher Titel, englischer Suchbegriff)
PROBES = {
    "rindergulasch": ("Rindergulasch", "beef goulash"),
    "haehnchen-curry": ("Hähnchen-Curry mit Reis", "chicken curry rice"),
    "spaghetti-bolognese": ("Spaghetti Bolognese", "spaghetti bolognese"),
    "kuerbissuppe": ("Kürbissuppe mit Ingwer", "pumpkin soup"),
    "kartoffelsalat": ("Amerikanischer Kartoffelsalat", "potato salad"),
    "lachs-ofen": ("Lachs aus dem Ofen mit Gemüse", "baked salmon vegetables"),
    "pfannkuchen": ("Pfannkuchen mit Ahornsirup", "pancakes maple syrup"),
    "gemuese-lasagne": ("Gemüselasagne", "vegetable lasagna"),
    "chili-con-carne": ("Chili con Carne", "chili con carne"),
    "apfelkuchen": ("Apfelkuchen", "apple pie"),
    "linsensuppe": ("Linsensuppe", "lentil soup"),
    "burger": ("Klassischer Burger", "cheeseburger"),
    "risotto": ("Pilzrisotto", "mushroom risotto"),
    "nudelsalat": ("Nudelsalat", "pasta salad"),
}


def search(query: str, want: int = 6) -> list[dict]:
    params = {
        "q": query,
        "license": "cc0,by,by-sa",
        "page_size": want,
        "mature": "false",
        "filter_dead": "false",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("results", [])


def pick(results: list[dict]) -> dict | None:
    """Nimmt das größte Bild mit brauchbarem Seitenverhältnis."""
    best, best_score = None, 0
    for r in results:
        w, h = r.get("width") or 0, r.get("height") or 0
        if w < 800 or h < 500:
            continue
        ratio = w / h if h else 0
        if not (1.1 <= ratio <= 2.0):  # quer, nicht extrem breit
            continue
        score = min(w, 2000) * (1.0 if ratio >= 1.3 else 0.85)
        if score > best_score:
            best, best_score = r, score
    return best


credits = {}
if CREDITS.exists():
    credits = json.loads(CREDITS.read_text())

for slug, (titel, query) in PROBES.items():
    dest = OUT / f"{slug}.webp"
    if dest.exists():
        print(f"skip {slug} (vorhanden)")
        continue
    try:
        results = search(query)
        hit = pick(results)
        if not hit:
            print(f"KEIN BRAUCHBARES BILD: {slug} ({len(results)} Treffer)")
            continue

        req = urllib.request.Request(hit["url"], headers={"User-Agent": UA})
        raw = urllib.request.urlopen(req, timeout=40).read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")

        # Auf 1200 px Breite bringen, mittig auf 3:2 beschneiden (einheitlich).
        target_ratio = 3 / 2
        w, h = img.size
        if w / h > target_ratio:
            new_w = int(h * target_ratio)
            img = img.crop(((w - new_w) // 2, 0, (w + new_w) // 2, h))
        else:
            new_h = int(w / target_ratio)
            img = img.crop((0, (h - new_h) // 2, w, (h + new_h) // 2))
        img = img.resize((1200, 800), Image.LANCZOS)
        img.save(dest, "WEBP", quality=82, method=6)

        credits[slug] = {
            "titel": titel,
            "query": query,
            "datei": f"/food/{slug}.webp",
            "creator": hit.get("creator"),
            "license": hit.get("license"),
            "license_version": hit.get("license_version"),
            "source": hit.get("source"),
            "foreign_landing_url": hit.get("foreign_landing_url"),
            "original_titel": hit.get("title"),
        }
        kb = dest.stat().st_size // 1024
        print(f"ok   {slug:22s} {kb:4d} KB  {hit.get('license'):7s} {str(hit.get('creator'))[:28]}")
        time.sleep(1.0)
    except Exception as e:
        print(f"FEHLER {slug}: {type(e).__name__} {e}")

CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n{len(credits)} Bilder in {OUT}")
