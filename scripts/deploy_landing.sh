#!/usr/bin/env bash
# Sprossa – Landingpage nach Produktion deployen (sprossa.de)
#
# Ablauf: Backup auf dem Server → rsync dist/landing → Verifikation via HTTPS.
# Rollback: das Backup liegt als /root/landing_backup_<TS>.tgz auf dem Server:
#   ssh root@2.31.17.36 "cd /opt/sprossa && rm -rf landing && tar xzf /root/landing_backup_<TS>.tgz"
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/dist/landing"
HOST="${SPROSSA_PROD_HOST:-root@2.31.17.36}"
DEST="/opt/sprossa/landing"
TS="$(date +%Y%m%d_%H%M%S)"

[ -f "$SRC/index.html" ] || { echo "FEHLER: $SRC/index.html fehlt – erst scripts/build_landing.sh" >&2; exit 1; }

echo "[landing-deploy] 1/4 – Backup auf $HOST"
ssh -o BatchMode=yes "$HOST" "tar czf /root/landing_backup_${TS}.tgz -C /opt/sprossa landing && ls -lh /root/landing_backup_${TS}.tgz"

echo "[landing-deploy] 2/4 – Upload nach $DEST"
rsync -az --delete -e "ssh -o BatchMode=yes" "$SRC"/ "$HOST:$DEST"/

echo "[landing-deploy] 3/4 – Rechte setzen"
ssh -o BatchMode=yes "$HOST" "chown -R root:root $DEST && find $DEST -type d -exec chmod 755 {} \; && find $DEST -type f -exec chmod 644 {} \;"

echo "[landing-deploy] 4/4 – Verifikation"
CODE="$(curl -s -o /tmp/landing_live.html -w '%{http_code}' -m 20 https://sprossa.de/)"
echo "  HTTP $CODE  ($(stat -c %s /tmp/landing_live.html) Bytes)"
grep -q 'Sprossa-Landingpage-Build:' /tmp/landing_live.html && echo "  ✓ Build-Marker im Live-HTML" || echo "  ! Build-Marker nicht gefunden"
grep -q 'viewBox="0 0 100 130"' /tmp/landing_live.html && echo "  ✓ Spross-SVG live" || { echo "  ✗ Spross-SVG fehlt live" >&2; exit 1; }
CSS="$(grep -o '/_next/static/css/[^"?]*' /tmp/landing_live.html | head -1)"
curl -s -m 20 "https://sprossa.de$CSS" | grep -q Fraunces && echo "  ✓ Fraunces im Live-CSS" || { echo "  ✗ Fraunces fehlt im Live-CSS" >&2; exit 1; }
grep -q 'flex-col gap-3 sm:flex-row' /tmp/landing_live.html && echo "  ✓ Mobil gestapeltes Formular live" || echo "  ! Formular-Klasse nicht gefunden"
echo "[landing-deploy] OK – Backup: /root/landing_backup_${TS}.tgz"
