#!/usr/bin/env python3
"""Übernimmt die generierten Bilder in die App: WebP, DB und Aufräumen.

Quelle: tmp/comfy_batch/scores.json (je Rezept die gewählte Datei + Note).
Ziel:   frontend/public/food/<slug>.webp, 1200x800, WebP q86
        recipes.image_url = /food/<slug>.webp
"""
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

OUT = Path("/home/mrjaws/monatsmenue/tmp/comfy_batch")
FOOD = Path("/home/mrjaws/monatsmenue/frontend/public/food")
SCORES = json.loads((OUT / "scores.json").read_text())
RESULTS = json.loads((OUT / "results.json").read_text())
DB = "sprossa-test-db"

UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})


def slugify(text: str) -> str:
    s = text.translate(UMLAUTE).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "rezept"


FOOD.mkdir(parents=True, exist_ok=True)
uebernommen, verworfen = [], []
used = set()
for rid, sc in SCORES.items():
    note = sc.get("note")
    src = Path(sc.get("best") or "")
    if not src.exists() or (note or 9) > 3:
        verworfen.append((RESULTS.get(rid, {}).get("title"), note))
        continue
    title = RESULTS.get(rid, {}).get("title") or rid
    slug = slugify(title.split("–")[0])
    if slug in used:
        slug = f"{slug}-{rid[:4]}"
    used.add(slug)

    img = Image.open(src).convert("RGB")
    w, h = img.size
    tr = 3 / 2
    if w / h > tr:
        nw = int(h * tr)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / tr)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    dest = FOOD / f"{slug}.webp"
    img.resize((1200, 800), Image.LANCZOS).save(dest, "WEBP", quality=86, method=6)
    uebernommen.append((rid, f"/food/{slug}.webp", note, title))

print(f"übernommen: {len(uebernommen)} · verworfen: {len(verworfen)}")

# Alte Openverse-Bilder entfernen: alles im Ordner, was jetzt nicht referenziert wird
referenziert = {Path(p).name for _, p, _, _ in uebernommen}
entfernt = 0
for f in FOOD.glob("*.webp"):
    if f.name not in referenziert:
        f.unlink()
        entfernt += 1
print(f"alte Bilder entfernt: {entfernt}")

# DB aktualisieren
sql = ["BEGIN;", "UPDATE recipes SET image_url = NULL;"]
for rid, url, note, title in uebernommen:
    sql.append(f"UPDATE recipes SET image_url = '{url}' WHERE id = '{rid}';")
sql.append("COMMIT;")
sql.append("SELECT count(*) FROM recipes WHERE image_url IS NOT NULL;")
res = subprocess.run(
    ["docker", "exec", "-i", DB, "psql", "-U", "sprossa", "-d", "sprossa_test", "-t"],
    input="\n".join(sql), capture_output=True, text=True,
)
print("DB:", res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[:200])

# Manifest für den NAS-Upload und die Nachvollziehbarkeit
manifest = [{"rezept": t, "datei": f"{Path(p).name}", "note": n} for _, p, n, t in uebernommen]
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("Manifest:", OUT / "manifest.json")
for t, n in verworfen:
    print(f"  verworfen: {t} (Note {n})")
