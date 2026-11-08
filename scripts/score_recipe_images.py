#!/usr/bin/env python3
"""Bewertet die generierten Rezeptbilder und waehlt je Rezept die beste Variante.

Pro Rezept ein Kontaktabzug mit den Varianten und EIN Vision-Call.
Fortschritt in tmp/comfy_batch/scores.json. Vier parallele Worker.
"""
import base64
import io
import json
import re
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

OUT = Path("/home/mrjaws/monatsmenue/tmp/comfy_batch")
RESULTS = OUT / "results.json"
SCORES = OUT / "scores.json"
LOCK = threading.Lock()

KEY = None
for line in Path("/home/mrjaws/.hermes/profiles/sprossa-pm/.env").read_text().splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        KEY = line.split("=", 1)[1].strip().strip('"').strip("'")

PROMPT = """Auf dem Bild sind {n} Varianten eines Food-Fotos, nummeriert.

Gericht: {dish}

Bewerte jede Variante mit Schulnote 1-6 als Titelfoto einer kostenpflichtigen
Familien-Ernaehrungs-App. Kriterien: appetitlich, hochwertig, passendes Gericht,
keine Stoerfaktoren (Text, Logo, Haende, unscharf, unappetitlich).

Antworte KURZ in genau diesem Format, ohne Vorrede:
1: Note <1-6> - <max 10 Woerter>
2: Note <1-6> - <max 10 Woerter>
BESTE: <Nummer>
"""


def grid(files: list[Path]) -> bytes:
    cell_w, cell_h, pad = 520, 390, 8
    sheet = Image.new("RGB", (len(files) * (cell_w + pad) + pad, cell_h + 2 * pad), "#111")
    for i, f in enumerate(files):
        img = Image.open(f).convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)
        sheet.paste(img, (pad + i * (cell_w + pad), pad))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=86)
    return buf.getvalue()


def score(rec: dict) -> tuple[str, dict]:
    rid = rec["id"]
    files = [Path(p) for p in rec.get("files", []) if Path(p).exists()]
    if not files:
        return rid, {"note": None, "best": None, "raw": "keine Datei"}
    b64 = base64.b64encode(grid(files)).decode()
    body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": PROMPT.format(n=len(files), dish=rec["title"])},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]}], "max_tokens": 400}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    text = json.load(urllib.request.urlopen(req, timeout=180))["choices"][0]["message"]["content"]
    m = re.search(r"BESTE:\s*(\d+)", text)
    note = None
    if m:
        nm = re.search(rf"(?m)^\s*{m.group(1)}:\s*Note\s*([1-6])", text)
        note = int(nm.group(1)) if nm else None
    best = int(m.group(1)) if m else 1
    best = min(max(best, 1), len(files))
    return rid, {"note": note, "best": str(files[best - 1]), "raw": text[:400]}


def main() -> int:
    data = json.loads(RESULTS.read_text())
    todo = [dict(v, id=k) for k, v in data.items() if v.get("status") == "ok"]
    scores = json.loads(SCORES.read_text()) if SCORES.exists() else {}
    todo = [r for r in todo if r["id"] not in scores]
    print(f"{len(todo)} offen, {len(scores)} bereits bewertet", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rid, res in pool.map(score, todo):
            with LOCK:
                scores[rid] = res
                done += 1
                if done % 20 == 0:
                    SCORES.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"  {done}/{len(todo)}", flush=True)

    SCORES.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    notes = [s["note"] for s in scores.values() if s.get("note")]
    from collections import Counter
    print("Noten:", dict(sorted(Counter(notes).items())))
    print(f"Note <=3: {sum(1 for n in notes if n <= 3)} von {len(scores)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
