#!/usr/bin/env bash
# Sprossa – Landingpage-Build (statischer Export für die Produktion)
#
# Warum ein eigenes Skript:
#   Die Produktions-Landingpage (https://sprossa.de) wird von Caddy als reine
#   statische Seite ausgeliefert. Der normale App-Build (output: standalone) ist
#   dafür nicht verwendbar. Dieses Skript baut mit LANDING_BUILD=1 in das separate
#   distDir `.next-build` (damit der root-owned `.next` des Dev-Containers
#   unangetastet bleibt) und setzt daraus ein deploybares Verzeichnis zusammen.
#
# Ergebnis:  dist/landing/  (index.html + _next/static + public-Assets)
# Nächster Schritt:  scripts/deploy_landing.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FE="$REPO/frontend"
OUT="$REPO/dist/landing"

cd "$FE"

echo "[landing-build] 1/4 – Abhängigkeiten prüfen"
if [ ! -d node_modules ]; then
  echo "[landing-build] node_modules fehlt – npm ci"
  npm ci
fi

echo "[landing-build] 2/4 – next build (LANDING_BUILD=1, distDir=.next-build)"
rm -rf .next-build

# `next build` schreibt tsconfig.json und next-env.d.ts auf das Build-distDir um
# (z.B. .next-build/types). Für den Dev-Betrieb im Container sind diese Dateien
# aber auf `.next` gepolt – deshalb nach dem Build unverändert zurücklegen,
# auch wenn der Build fehlschlägt.
TSCONFIG_BAK="$(mktemp)"; NEXTENV_BAK="$(mktemp)"
cp tsconfig.json "$TSCONFIG_BAK" 2>/dev/null || true
cp next-env.d.ts "$NEXTENV_BAK" 2>/dev/null || true
restore_ts_config() {
  [ -s "$TSCONFIG_BAK" ] && cp "$TSCONFIG_BAK" tsconfig.json
  [ -s "$NEXTENV_BAK" ] && cp "$NEXTENV_BAK" next-env.d.ts
  rm -f "$TSCONFIG_BAK" "$NEXTENV_BAK"
}
trap restore_ts_config EXIT

LANDING_BUILD=1 npx next build
restore_ts_config
trap - EXIT

if [ ! -f .next-build/server/app/index.html ]; then
  echo "[landing-build] FEHLER: .next-build/server/app/index.html wurde nicht erzeugt" >&2
  exit 1
fi

echo "[landing-build] 3/4 – Deploy-Verzeichnis zusammensetzen: $OUT"
rm -rf "$OUT"
mkdir -p "$OUT/_next"

cp .next-build/server/app/index.html "$OUT/index.html"
cp -r .next-build/static/. "$OUT/_next/static/"

# Rechtsseiten als eigene Routen mit ausliefern (/impressum/, /datenschutz/, /agb/)
for page in impressum datenschutz agb bildnachweis; do
  if [ -f ".next-build/server/app/$page.html" ]; then
    mkdir -p "$OUT/$page"
    cp ".next-build/server/app/$page.html" "$OUT/$page/index.html"
  else
    echo "[landing-build] WARNUNG: $page.html wurde nicht erzeugt" >&2
  fi
done

# public/ (favicon.svg etc.) mitnehmen, falls vorhanden
if [ -d public ]; then
  cp -r public/. "$OUT/"
fi

# Version/Datum als Kommentar in die HTML (Nachvollziehbarkeit im Live-HTML)
STAMP="$(date -Iseconds)"
python3 - "$OUT/index.html" "$STAMP" <<'PY'
import sys
path, stamp = sys.argv[1], sys.argv[2]
html = open(path, encoding="utf-8").read()
marker = f"<!-- Sprossa-Landingpage-Build: {stamp} -->"
if "Sprossa-Landingpage-Build:" not in html:
    html = html.replace("<head>", "<head>" + marker, 1)
open(path, "w", encoding="utf-8").write(html)
PY

echo "[landing-build] 4/4 – Kontrolle"
echo "  HTML:  $(stat -c %s "$OUT/index.html") Bytes"
echo "  CSS:   $(ls "$OUT/_next/static/css" 2>/dev/null | wc -l) Datei(en)"
echo "  Chunks:$(ls "$OUT/_next/static/chunks" 2>/dev/null | wc -l) Datei(en)"
grep -q "Fraunces" "$OUT"/_next/static/css/*.css \
  && echo "  ✓ Fraunces im CSS" \
  || { echo "  ✗ Fraunces fehlt im CSS" >&2; exit 1; }
grep -q 'viewBox="0 0 100 130"' "$OUT/index.html" \
  && echo "  ✓ Spross-SVG im Header" \
  || { echo "  ✗ Spross-SVG fehlt" >&2; exit 1; }
echo "[landing-build] OK → $OUT"
