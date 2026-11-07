#!/usr/bin/env bash
# Richtet den täglichen Pageview-Löschjob als Cron ein.
#
# Aufruf auf dem jeweiligen Server:
#   ./scripts/install_purge_cron.sh <backend-container>
#
# Beispiel Produktion:  ./scripts/install_purge_cron.sh sprossa-backend-1
# Beispiel Testsystem:  ./scripts/install_purge_cron.sh sprossa-test-backend
#
# Die Datenschutzerklärung sagt 90 Tage Aufbewahrung zu. Ohne diesen Job
# wächst die Tabelle unbegrenzt und die Zusage wäre unwahr.
set -euo pipefail

CONTAINER="${1:-sprossa-backend-1}"
MARKER="# sprossa-pageview-purge"
CRON_LINE="23 4 * * * docker exec ${CONTAINER} python -m app.jobs.purge_pageviews >/dev/null 2>&1 ${MARKER}"

echo "Prüfe, ob der Job im Container läuft …"
if ! docker exec "$CONTAINER" python -m app.jobs.purge_pageviews; then
  echo "FEHLER: Job läuft nicht. Ist der Code im Container vorhanden?" >&2
  exit 1
fi

# Bestehende Zeile entfernen, dann neu anhängen (idempotent).
if crontab -l 2>/dev/null | grep -q "sprossa-pageview-purge"; then
  crontab -l 2>/dev/null | grep -v "sprossa-pageview-purge" | crontab -
fi
( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | crontab -

echo "Cron eingerichtet:"
crontab -l 2>/dev/null | grep "sprossa-pageview-purge"
