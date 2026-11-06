"""Wendet überarbeitete Kinder-Tipps auf die DB an.

Liest tmp/tip_batches/out_*.json, prüft jeden Eintrag gegen die Qualitätsregeln
und schreibt per UPDATE (nie DELETE). Ohne --apply nur Bericht.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

BATCH_DIR = Path("/home/mrjaws/monatsmenue/tmp/tip_batches")

MIN_LEN, MAX_LEN = 60, 420
TRIVIAL = re.compile(
    r"\b(holen|hol |sortieren|abzählen|zuschauen|dabeisein|wegräumen)\b",
    re.IGNORECASE,
)
# Teilstring-Suche ohne Wortgrenzen: Komposita wie "auseinanderzupfen" oder
# "unterheben" sollen treffen, auch wenn ein Praefix davorsitzt.
SENSORY = re.compile(
    r"(riechen|schmecken|kosten|probier|fühlen|anfassen|zerdrück|zerrupf|zerbrösel|zerstoss|"
    r"formen|kneten|bestreich|pell|zupf|drück|einreib|abzieh|ausstech|auseinander|unterheb|"
    r"brösel|streu|schicht|füll|wickel|roll|reib|schneid|brech|rühr|wasch|putz|beleg|misch|"
    r"abtupf|aushöhl|auspress|löffel|wende|zieh|hobel|raspel)",
    re.IGNORECASE,
)
# "abnehmen" bewusst NICHT drin: im Kochkontext heisst es "Portion abnehmen".
BANNED = re.compile(r"\b(gesund|gesünder|vitaminreich|Küchenheld|Abenteuer)\b", re.IGNORECASE)


def load() -> list[dict]:
    """Liest die Batch-Ergebnisse. Ein Batch kann als Array oder als Objekt
    mit id/new_tip vorliegen."""
    items = []
    for f in sorted(BATCH_DIR.glob("out_*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("items") or data.get("eintraege") or []
            if data and isinstance(data[0], dict) and "new_tip" not in data[0]:
                data = []
        if not isinstance(data, list):
            raise SystemExit(f"{f.name}: unerwartetes Format")
        items.extend([d for d in data if isinstance(d, dict) and "new_tip" in d])
    return items


def check(item: dict) -> list[str]:
    problems = []
    tip = (item.get("new_tip") or "").strip()
    if not item.get("id"):
        problems.append("keine id")
    if not tip:
        problems.append("leerer Text")
        return problems
    if len(tip) < MIN_LEN:
        problems.append(f"zu kurz ({len(tip)})")
    if len(tip) > MAX_LEN:
        problems.append(f"zu lang ({len(tip)})")
    if TRIVIAL.search(tip):
        problems.append("triviale Aufgabe")
    if not SENSORY.search(tip):
        problems.append("kein sinnlicher Anker")
    if BANNED.search(tip):
        problems.append("verbotene Formulierung")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    items = load()
    print(f"Einträge geladen: {len(items)}")

    ids = [i.get("id") for i in items]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"WARNUNG: {len(dupes)} doppelte IDs")

    bad = {}
    ok = 0
    for it in items:
        p = check(it)
        if p:
            bad.setdefault(tuple(p), []).append(it.get("id", "?"))
        else:
            ok += 1

    print(f"sauber: {ok} · auffällig: {len(items) - ok}")
    for k, v in sorted(bad.items(), key=lambda x: -len(x[1])):
        print(f"  {', '.join(k)}: {len(v)}")

    schema = sum(1 for i in items if (i.get("new_tip") or "").lower().startswith("die kinder können"))
    anteil = schema * 100 // max(1, len(items))
    print(f"Schema-Anfang 'Die Kinder koennen': {schema} ({anteil} %)")

    if not args.apply:
        print("\nDry-Run — nichts geschrieben. Mit --apply anwenden.")
        return 0

    # UPDATE per psql, eine Transaktion
    lines = ["BEGIN;"]
    for it in items:
        tip = (it["new_tip"] or "").strip().replace("'", "''")
        lines.append(f"UPDATE recipes SET kid_friendly_tip = '{tip}' WHERE id = '{it['id']}';")
    lines.append("COMMIT;")
    sql = "\n".join(lines)

    r = subprocess.run(
        ["docker", "exec", "-i", "sprossa-test-db", "psql", "-U", "sprossa", "-d", "sprossa_test", "-v", "ON_ERROR_STOP=1"],
        input=sql, capture_output=True, text=True,
    )
    print(r.stdout[-800:])
    if r.returncode != 0:
        print("FEHLER:", r.stderr[-1200:])
        return 1
    print("angewandt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
