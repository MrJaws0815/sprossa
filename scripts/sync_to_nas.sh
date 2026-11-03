#!/usr/bin/env bash
# Sprossa – Projektdateien auf den Netzlaufwerk-Share spiegeln.
#
# Zielstruktur (\\HOMENAS\Sprossa):
#   01_Marke_und_Design/  Logo, Social-Assets, Vorlagen (HTML-Templates + Copy)
#   02_Content/Pins/      strategisch (4 finale) + serien (20 generische)
#   02_Content/Reels/     Keyframes (PNG) + Footage (MP4)
#   03_Technik/           Landingpage-Build, Backups
#   04_Projektleitung/    Projektplan + PM-Dokumente (Snapshot)
#
# Idempotent: mehrfaches Ausführen überschreibt, löscht nichts.

set -euo pipefail

VAULT="/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa"
REPO="/home/mrjaws/monatsmenue"
NAS="${NAS_MOUNT:-/mnt/sprossa}"

[ -d "$NAS" ] || { echo "FEHLER: $NAS nicht gemountet" >&2; exit 1; }

say() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$1"; }

say "1/4 – Marke und Design"
mkdir -p "$NAS/01_Marke_und_Design/Logo" \
         "$NAS/01_Marke_und_Design/Social-Assets" \
         "$NAS/01_Marke_und_Design/Vorlagen"
cp -f "$VAULT/03 Marke & Design/Logo/"*.svg "$NAS/01_Marke_und_Design/Logo/" 2>/dev/null || true
cp -f "$VAULT/03 Marke & Design/Social-Assets/"* "$NAS/01_Marke_und_Design/Social-Assets/" 2>/dev/null || true
for f in "Sprossa - Pinterest-Pin-Vorlagen.html" \
         "Sprossa Reel-Vorlagen Preview.html" \
         "Sprossa - Strategische Pins v3.0.html" \
         "Sprossa - Strategische Pins v3.0 - Copy.txt"; do
  [ -f "$VAULT/03 Marke & Design/$f" ] && cp -f "$VAULT/03 Marke & Design/$f" "$NAS/01_Marke_und_Design/Vorlagen/"
done
echo "  Logo: $(ls -1 "$NAS/01_Marke_und_Design/Logo" | wc -l) Dateien"
echo "  Social: $(ls -1 "$NAS/01_Marke_und_Design/Social-Assets" | wc -l) Dateien"
echo "  Vorlagen: $(ls -1 "$NAS/01_Marke_und_Design/Vorlagen" | wc -l) Dateien"

say "2/4 – Content (Pins und Reels)"
mkdir -p "$NAS/02_Content/Pins/strategisch" \
         "$NAS/02_Content/Pins/serien" \
         "$NAS/02_Content/Reels/Keyframes" \
         "$NAS/02_Content/Reels/Footage"
cp -f "$REPO/dist/pins-strategisch/"*.png "$NAS/02_Content/Pins/strategisch/" 2>/dev/null || true
cp -f "$REPO/dist/pins/"*.png "$NAS/02_Content/Pins/serien/" 2>/dev/null || true
cp -f "$REPO/dist/reels/"*.png "$NAS/02_Content/Reels/Keyframes/" 2>/dev/null || true
if [ -f "$REPO/dist/footage/strategische-pins.mp4" ]; then
  cp -f "$REPO/dist/footage/strategische-pins.mp4" "$NAS/02_Content/Reels/Footage/"
fi
echo "  Strategische Pins: $(ls -1 "$NAS/02_Content/Pins/strategisch" | wc -l)"
echo "  Serien-Pins: $(ls -1 "$NAS/02_Content/Pins/serien" | wc -l)"
echo "  Keyframes: $(ls -1 "$NAS/02_Content/Reels/Keyframes" | wc -l)"
echo "  Footage: $(ls -1 "$NAS/02_Content/Reels/Footage" 2>/dev/null | wc -l)"

say "3/4 – Technik"
mkdir -p "$NAS/03_Technik/Landingpage-Build" "$NAS/03_Technik/Backups"
if [ -d "$REPO/dist/landing" ]; then
  cp -rf "$REPO/dist/landing/." "$NAS/03_Technik/Landingpage-Build/"
fi
echo "  Landingpage-Dateien: $(find "$NAS/03_Technik/Landingpage-Build" -type f | wc -l)"

say "4/4 – Projektleitung (Snapshot der PM-Dokumente)"
mkdir -p "$NAS/04_Projektleitung"
for f in "01 Projektleitung/Sprossa Projektplan.md" \
         "01 Projektleitung/Sprossa - SaaS PM Briefing - Data & UX.md" \
         "01 Projektleitung/Sprossa - Datenmodell Nutzerprofile.md"; do
  [ -f "$VAULT/$f" ] && cp -f "$VAULT/$f" "$NAS/04_Projektleitung/"
done
echo "  Dokumente: $(ls -1 "$NAS/04_Projektleitung" | wc -l)"

say "5/5 – Dokumentation (Markdown-Snapshot des Obsidian-Vaults)"
mkdir -p "$NAS/05_Dokumentation/Obsidian-Vault"
# AppleDouble-Dateien (._*) und .DS_Store scheitern über CIFS – ausschließen.
rsync -a --exclude="._*" --exclude=".DS_Store" \
      --include="*/" --include="*.md" --exclude="*" \
      "$VAULT/" "$NAS/05_Dokumentation/Obsidian-Vault/" 2>/dev/null || {
  # Fallback: rsync kann bei Umlauten im Dateinamen über CIFS abbrechen,
  # dann per find+cp einzeln kopieren.
  find "$VAULT" -name "*.md" -print0 | while IFS= read -r -d '' f; do
    rel="${f#$VAULT/}"
    mkdir -p "$NAS/05_Dokumentation/Obsidian-Vault/$(dirname "$rel")"
    cp -f "$f" "$NAS/05_Dokumentation/Obsidian-Vault/$rel"
  done
}
echo "  Markdown-Notizen: $(find "$NAS/05_Dokumentation/Obsidian-Vault" -name '*.md' | wc -l)"

say "Fertig. Gesamtgröße auf dem Share:"
du -sh "$NAS" 2>/dev/null
