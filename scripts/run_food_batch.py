#!/usr/bin/env python3
"""Batch: lizenzfreies Titelbild für jedes Rezept.

Nutzt scripts/openverse_pick.py (Skill `licensed-image-sourcing`) pro Rezept:
Openverse-Suche -> Auflösungsfilter -> Kontaktabzug -> Vision-Auswahl ->
Original zuschneiden -> Credits.

Fortschritt steht in tmp/food_batch_results.json; ein Abbruch ist unschädlich,
ein erneuter Lauf macht dort weiter.

    python3 scripts/run_food_batch.py            # alle Rezepte
    python3 scripts/run_food_batch.py --limit 15 # nur die ersten 15 (Probelauf)
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DB_CONTAINER = "sprossa-test-db"
OUT_DIR = Path("/home/mrjaws/monatsmenue/frontend/public/food")
CREDITS = Path("/home/mrjaws/monatsmenue/tmp/food_credits.json")
RESULTS = Path("/home/mrjaws/monatsmenue/tmp/food_batch_results.json")
PICKER = Path("/home/mrjaws/.hermes/profiles/sprossa-pm/skills/licensed-image-sourcing/scripts/openverse_pick.py")

UMLAUTE = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss",
})


def slugify(text: str) -> str:
    s = text.translate(UMLAUTE).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "rezept"


def queries_for(title: str) -> list[str]:
    """Suchbegriffe vom genauesten zum gröbsten.

    Reihenfolge ist wichtig: Ein Fallback auf das erste Wort greift bei
    deutschen Gerichten ins Leere ("Amerikanischer Kartoffelsalat" ->
    "Amerikanischer" -> Insektenfotos). Das Grundwort steht im Deutschen
    meist am Ende.
    """
    base = re.sub(r"\([^)]*\)", "", title)
    base = re.sub(r"\b(selbst gemacht|selbstgemacht|hausgemacht)\b", "", base, flags=re.I)
    base = base.strip(" ,–-")

    out = [base]

    # "X mit Y" / "X in Y" / "X auf Y" -> nur X
    short = re.split(r"\s+(mit|in|auf|aus|nach)\s+", base, maxsplit=1)[0].strip(" ,–-")
    if short and short != base:
        out.append(short)

    # Grundwort = letztes Wort ("Amerikanischer Kartoffelsalat" -> "Kartoffelsalat")
    parts = [p for p in re.split(r"[\s-]+", short or base) if p]
    if len(parts) > 1:
        out.append(parts[-1])

    # Adjektiv am Anfang abwerfen, Rest behalten
    if len(parts) > 1 and re.search(r"(er|isch|lich|ig|es|e)$", parts[0], re.I):
        out.append(" ".join(parts[1:]))

    seen, uniq = set(), []
    for q in out:
        if q and q.lower() not in seen:
            seen.add(q.lower())
            uniq.append(q)
    return uniq


def load_recipes() -> list[tuple[str, str]]:
    sql = "SELECT id, title FROM recipes ORDER BY title;"
    res = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "sprossa", "-d", "sprossa_test", "-t", "-A", "-F", "|", "-c", sql],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise SystemExit(f"DB-Abfrage fehlgeschlagen: {res.stderr[:300]}")
    rows = []
    for line in res.stdout.strip().splitlines():
        if "|" in line:
            rid, title = line.split("|", 1)
            rows.append((rid.strip(), title.strip()))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N Rezepte")
    ap.add_argument("--min-width", type=int, default=1200)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    if RESULTS.exists():
        results = json.loads(RESULTS.read_text(encoding="utf-8"))

    recipes = load_recipes()
    if args.limit:
        recipes = recipes[: args.limit]
    print(f"{len(recipes)} Rezepte, bereits bearbeitet: {sum(1 for v in results.values() if v.get('status') == 'ok')}", flush=True)

    used_slugs: set[str] = set()
    for idx, (rid, title) in enumerate(recipes, 1):
        slug = slugify(title)
        if slug in used_slugs or (slug in results and results[slug].get("status") == "ok"):
            if results.get(slug, {}).get("status") == "ok" and results.get(slug, {}).get("rezept") == title:
                continue
            slug = f"{slug}-{rid[:4]}"
        used_slugs.add(slug)

        if results.get(slug, {}).get("status") in ("ok", "none"):
            continue

        print(f"\n[{idx}/{len(recipes)}] {title}  ->  {slug}", flush=True)
        status, note, detail = "none", None, ""
        for query in queries_for(title):
            cmd = [
                sys.executable, str(PICKER),
                "--query", query, "--slug", slug,
                "--out-dir", str(OUT_DIR), "--credits", str(CREDITS),
                "--min-width", str(args.min_width),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            out = (proc.stdout or "") + (proc.stderr or "")
            m = re.search(r"BESTE:\s*(\d+)", out)
            if proc.returncode == 0:
                status, detail = "ok", f"query={query}"
                # Note der gewaehlten Nummer aus "NOTEN: 01:4, 02:2" lesen
                if m:
                    notes = next(
                        (ln for ln in out.splitlines() if ln.strip().upper().startswith("NOTEN:")), ""
                    )
                    mm = re.search(rf"\b0*{int(m.group(1))}:(\d)", notes)
                    note = int(mm.group(1)) if mm else None
                break
            # 2 = kein Kandidat -> naechster, groeberer Suchbegriff
            if proc.returncode != 2:
                detail = out.strip().splitlines()[-1][:200] if out.strip() else "unbekannt"
                break

        results[slug] = {
            "rezept": title, "status": status, "note": note,
            "rezept_id": rid, "detail": detail,
        }
        RESULTS.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    -> {status} (Note {note}) {detail}", flush=True)
        time.sleep(1.5)

    ok = [k for k, v in results.items() if v.get("status") == "ok"]
    none = [k for k, v in results.items() if v.get("status") == "none"]
    print(f"\nFertig: {len(ok)} mit Bild, {len(none)} ohne. Datei: {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
