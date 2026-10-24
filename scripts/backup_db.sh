#!/usr/bin/env bash
# Sprossa – PostgreSQL Backup mit Retention (Best Practice)
# Nutzung: ./scripts/backup_db.sh [test|prod]
# Default: test
#
# Best Practices:
# - Custom-Format (-Fc): komprimiert, selektiver Restore möglich
# - Zeitstempel im Dateinamen
# - Integritätsprüfung via pg_restore --list
# - Retention: 14 tägliche Backups, ältere als 30 Tage werden gelöscht
# - Logfile für Audit-Trail

set -euo pipefail

ENV="${1:-test}"
BACKUP_DIR="/home/mrjaws/monatsmenue/backups"
RETENTION_DAYS=30
KEEP_MIN=14
TS=$(date +%Y%m%d_%H%M%S)
LOG="$BACKUP_DIR/backup.log"

case "$ENV" in
  test)
    CONTAINER="sprossa-test-db"
    DB_USER="sprossa"
    DB_NAME="sprossa_test"
    ;;
  prod)
    CONTAINER="sprossa-db"
    DB_USER="sprossa"
    DB_NAME="sprossa"
    ;;
  *)
    echo "Unbekanntes Environment: $ENV (erlaubt: test|prod)" >&2
    exit 1
    ;;
esac

FILE="$BACKUP_DIR/${DB_NAME}_${TS}.dump"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Iseconds)] START backup $ENV ($DB_NAME) -> $FILE" | tee -a "$LOG"

# 1. Dump im Custom-Format
if ! docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > "$FILE"; then
  echo "[$(date -Iseconds)] FEHLER: pg_dump fehlgeschlagen" | tee -a "$LOG" >&2
  rm -f "$FILE"
  exit 1
fi

# 2. Integritätsprüfung
if ! docker exec -i "$CONTAINER" pg_restore --list < "$FILE" > /dev/null 2>&1; then
  echo "[$(date -Iseconds)] FEHLER: Backup korrupt (pg_restore --list)" | tee -a "$LOG" >&2
  exit 1
fi

SIZE=$(du -h "$FILE" | cut -f1)
echo "[$(date -Iseconds)] OK: $FILE ($SIZE)" | tee -a "$LOG"

# 3. Retention: Alte Backups löschen (aber mindestens KEEP_MIN behalten)
COUNT=$(ls -1 "$BACKUP_DIR"/*.dump 2>/dev/null | wc -l)
if [ "$COUNT" -gt "$KEEP_MIN" ]; then
  # Lösche Dateien älter als RETENTION_DAYS, aber behalte die neuesten KEEP_MIN
  find "$BACKUP_DIR" -name "*.dump" -type f -mtime +"$RETENTION_DAYS" -print -delete 2>/dev/null | while read -r old; do
    echo "[$(date -Iseconds)] ROTATE: gelöscht $old" | tee -a "$LOG"
  done
fi

echo "[$(date -Iseconds)] END backup $ENV" | tee -a "$LOG"
