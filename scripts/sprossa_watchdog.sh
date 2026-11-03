#!/usr/bin/env bash
# Sprossa-Watchdog: prüft Produktion und Backup-Kette.
# Gibt NICHTS aus, wenn alles in Ordnung ist (stiller Watchdog).
# Bei Problemen: kurze Meldung auf stdout -> wird als Nachricht zugestellt.
set -uo pipefail

PROBLEMS=""

code=$(curl -s -o /dev/null -w '%{http_code}' -m 15 https://sprossa.de/ || echo 000)
[ "$code" = "200" ] || PROBLEMS="${PROBLEMS}- Landingpage: HTTP ${code}\n"

code=$(curl -s -o /dev/null -w '%{http_code}' -m 15 https://sprossa.de/api/v1/waitlist/count || echo 000)
[ "$code" = "200" ] || PROBLEMS="${PROBLEMS}- API waitlist/count: HTTP ${code}\n"

code=$(curl -s -o /dev/null -w '%{http_code}' -m 15 https://sprossa.de/impressum/ || echo 000)
[ "$code" = "200" ] || PROBLEMS="${PROBLEMS}- Impressum: HTTP ${code}\n"

if ! mountpoint -q /mnt/sprossa; then
  PROBLEMS="${PROBLEMS}- NAS nicht gemountet (/mnt/sprossa)\n"
else
  NEWEST=$(ls -1t /mnt/sprossa/06_Backups/sprossa-prod/sprossa_*.dump 2>/dev/null | head -1)
  if [ -z "$NEWEST" ]; then
    PROBLEMS="${PROBLEMS}- Kein Produktions-Backup auf dem NAS\n"
  else
    AGE_H=$(( ( $(date +%s) - $(stat -c %Y "$NEWEST") ) / 3600 ))
    [ "$AGE_H" -gt 36 ] && PROBLEMS="${PROBLEMS}- Letztes Backup ist ${AGE_H} h alt\n"
  fi
fi

USE=$(timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=10 root@2.31.17.36 "df --output=pcent / | tail -1 | tr -dc '0-9'" 2>/dev/null)
if [ -n "${USE:-}" ] && [ "$USE" -gt 85 ]; then
  PROBLEMS="${PROBLEMS}- Server-Disk bei ${USE}%\n"
fi

DUMP=$(ls -1t /mnt/sprossa/06_Backups/sprossa-prod/sprossa_*.dump 2>/dev/null | head -1)
if [ -n "$DUMP" ] && [ "$(head -c 5 "$DUMP")" != "PGDMP" ]; then
  PROBLEMS="${PROBLEMS}- Neuestes Backup ist keine gültige pg_dump-Datei\n"
fi

if [ -n "$PROBLEMS" ]; then
  printf 'Sprossa Watchdog – %s\n\n%b' "$(date '+%d.%m.%Y %H:%M')" "$PROBLEMS"
  printf '\nLetztes Backup: %s\n' "$(basename "$DUMP" 2>/dev/null || echo '–')"
fi
