"""Holt Fraunces und Nunito als woff2 und erzeugt eine lokale fonts.css.

Der Abruf passiert einmalig hier (Build-Zeit). Zur Laufzeit geht kein
Request mehr an Google - das ist der Punkt: Die IP der Nutzer bleibt bei
uns (LG Muenchen I, 2022: dynamisches Laden ohne Einwilligung ist
rechtswidrig).
"""
import re
import urllib.request
from pathlib import Path

OUT = Path("/home/mrjaws/monatsmenue/frontend/public/fonts")
OUT.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Nunito:wght@400;600;700;800&family=Fraunces:wght@400;600;700&display=swap"
)

req = urllib.request.Request(URL, headers={"User-Agent": UA})
css = urllib.request.urlopen(req, timeout=30).read().decode()

# Nur die Subsets behalten, die Deutsch brauchen.
blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
keep = {"latin", "latin-ext"}
picked = [(subset, block) for subset, block in blocks if subset in keep]
print(f"Blöcke gesamt: {len(blocks)}, behalten: {len(picked)}")

out_css = []
seen = {}
for subset, block in picked:
    fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
    weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
    style = re.search(r"font-style:\s*(\w+)", block).group(1)
    src = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)

    fname = f"{fam.lower()}-{weight}-{style}-{subset}.woff2"
    dest = OUT / fname
    if fname not in seen:
        data = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": UA}), timeout=30).read()
        dest.write_bytes(data)
        seen[fname] = len(data)
        print(f"  {fname:44s} {len(data)//1024} KB")

    out_css.append(
        f"@font-face {{\n"
        f"  font-family: '{fam}';\n"
        f"  font-style: {style};\n"
        f"  font-weight: {weight};\n"
        f"  font-display: swap;\n"
        f"  src: url('/fonts/{fname}') format('woff2');\n"
        f"  unicode-range: {re.search(r'unicode-range:\s*([^;]+);', block).group(1)};\n"
        f"}}\n"
    )

(OUT / "fonts.css").write_text("\n".join(out_css), encoding="utf-8")
print(f"\n{len(seen)} Dateien, {len(out_css)} @font-face-Regeln")
