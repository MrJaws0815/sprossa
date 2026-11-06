"""Exportiert Rezeptdaten in Batches für die Kinder-Tipp-Überarbeitung.

Nutzt json_agg, weil psql -A bei mehrzeiligen Feldern (instructions) sonst
Zeilenumbrüche in die Ausgabe schreibt und der Zeilenparser Rezepte verschluckt.
"""
import json
import subprocess
from pathlib import Path

SQL = """
SELECT coalesce(json_agg(row_to_json(t) ORDER BY t.title), '[]'::json)::text
FROM (
  SELECT r.id,
         r.title,
         r.servings,
         left(coalesce(r.instructions,''), 700) AS instructions,
         coalesce(r.kid_friendly_tip,'') AS old_tip,
         coalesce(string_agg(i.name, ' | ' ORDER BY i.name), '') AS ingredients
  FROM recipes r
  LEFT JOIN recipe_ingredients ri ON ri.recipe_id = r.id
  LEFT JOIN ingredients i ON i.id = ri.ingredient_id
  GROUP BY r.id, r.title, r.servings, r.instructions, r.kid_friendly_tip
) t;
"""

raw = subprocess.run(
    ["docker", "exec", "sprossa-test-db", "psql", "-U", "sprossa", "-d", "sprossa_test",
     "-t", "-A", "-c", SQL],
    capture_output=True, text=True, check=True,
).stdout.strip()

rows = json.loads(raw)
for r in rows:
    r["instructions"] = " ".join((r.get("instructions") or "").split())

outdir = Path("/home/mrjaws/monatsmenue/tmp/tip_batches")
outdir.mkdir(parents=True, exist_ok=True)
for old in outdir.glob("batch_*.json"):
    old.unlink()

N = 5
size = (len(rows) + N - 1) // N
for i in range(N):
    batch = rows[i * size:(i + 1) * size]
    if not batch:
        continue
    path = outdir / f"batch_{i+1}.json"
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{path.name}: {len(batch)} Rezepte, {path.stat().st_size // 1024} KB")

print("gesamt:", len(rows))
