"""Exportiert alle Kinder-Tipps und bewertet sie nach Qualitätsmustern."""
import json
import re
import subprocess

SQL = """
SELECT id, title, coalesce(kid_friendly_tip,''), tags::text
FROM recipes ORDER BY title;
"""

out = subprocess.run(
    ["docker", "exec", "sprossa-test-db", "psql", "-U", "sprossa", "-d", "sprossa_test",
     "-t", "-A", "-F", "\x1f", "-c", SQL],
    capture_output=True, text=True, check=True,
).stdout

# Triviale Aufgaben: nichts, was wirklich hilft
TRIVIAL = re.compile(
    r"\b(holen|hol|sortieren|zählen|zählen lassen|abzählen|in den kühlschrank|"
    r"aus dem kühlschrank|anschauen|angucken|beobachten|zuschauen|dabeisein|"
    r"aussuchen|auswählen|runternehmen|wegräumen|abwaschen)\b",
    re.IGNORECASE,
)
# Sensorische Anker: riechen, schmecken, fühlen, kneten
SENSORY = re.compile(r"\b(riechen|schmecken|kosten|fühlen|kneten|matschen|zerdrücken|zerrupfen)\b", re.IGNORECASE)
# Sicherheitshinweis
SAFETY = re.compile(r"\b(aufsicht|vorsichtig|stumpf|kalt|abkühlen|nicht anfassen|heiß)\b", re.IGNORECASE)


def classify(tip: str) -> str:
    t = tip.strip()
    if not t:
        return "leer"
    low = t.lower()
    if len(t) < 45:
        return "zu_kurz"
    if TRIVIAL.search(low):
        return "trivial"
    if low.startswith("die kinder können") and not SENSORY.search(low):
        return "schema_ohne_sensorik"
    if SENSORY.search(low) or SAFETY.search(low):
        return "konkret"
    return "unbestimmt"


rows = []
for line in out.splitlines():
    if not line.strip():
        continue
    parts = line.split("\x1f")
    if len(parts) < 4:
        continue
    rid, title, tip, tags = parts[0], parts[1], parts[2], parts[3]
    rows.append({"id": rid, "title": title, "tip": tip, "tags": tags, "klasse": classify(tip)})

from collections import Counter
c = Counter(r["klasse"] for r in rows)
print("Gesamt:", len(rows))
for k, v in c.most_common():
    print(f"  {k:22s} {v}")

with open("/home/mrjaws/monatsmenue/tmp/kinder_tipps.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print("\n--- Beispiele pro Klasse ---")
seen = set()
for r in rows:
    if r["klasse"] in seen:
        continue
    seen.add(r["klasse"])
    print(f"[{r['klasse']}] {r['title'][:44]}: {r['tip'][:110]}")
