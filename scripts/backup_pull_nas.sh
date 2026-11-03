#!/usr/bin/env bash
# Sprossa – Produktions-Backups vom Server aufs NAS spiegeln (Pull vom Pi).
# Läuft täglich 04:15 auf dem Pi, nachdem der Server-Dump um 03:30 gelaufen ist.
# Aufbewahrung auf dem NAS: 30 tägliche Dumps. Auf dem Server bleiben nur 3.
set -euo pipefail

SRC="root@2.31.17.36:/opt/sprossa/backups/"
DEST="/mnt/sprossa/06_Backups/sprossa-prod"
LOG="$DEST/pull.log"
KEEP=30

mkdir -p "$DEST"
if ! mountpoint -q /mnt/sprossa; then
  echo "[$(date -Iseconds)] FEHLER NAS nicht gemountet" >> "$LOG"
  exit 1
fi

echo "[$(date -Iseconds)] START pull" >> "$LOG"
if ! rsync -az --include='sprossa_*.dump' --exclude='*' \
     -e "ssh -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new" \
     "$SRC" "$DEST/" >> "$LOG" 2>&1; then
  echo "[$(date -Iseconds)] FEHLER rsync" >> "$LOG"
  exit 1
fi

NEWEST="$(ls -1t "$DEST"/sprossa_*.dump 2>/dev/null | head -1 || true)"
if [ -z "$NEWEST" ]; then
  echo "[$(date -Iseconds)] FEHLER kein Dump angekommen" >> "$LOG"
  exit 1
fi

MAGIC="$(head -c 5 "$NEWEST")"
if [ "$MAGIC" != "PGDMP" ]; then
  echo "[$(date -Iseconds)] FEHLER Dump-Format ungültig: $NEWEST" >> "$LOG"
  exit 1
fi

# Retention auf dem NAS
ls -1t "$DEST"/sprossa_*.dump 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "[$(date -Iseconds)] OK $(basename "$NEWEST") $(stat -c %s "$NEWEST") bytes" >> "$LOG"
