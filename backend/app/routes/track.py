"""Traffic-Tracking für die Landingpage (pageview) und internes Dashboard.

- POST /track/pageview  → öffentlich, nimmt Seitenaufrufe von sprossa.de entgegen.
  Datensparsam: keine IP, kein Cookie. `session_hash` = täglicher Hash aus
  IP + User-Agent + Datum → eindeutige Besucher zählbar, ohne Personendaten.
- GET  /track/dashboard → intern, HTTP-Basic-Auth. Liefert aggregierte Kennzahlen
  als JSON; die HTML-Ansicht baut die Route /track/dashboard/view.

Sicherheit: Das Dashboard hängt an `/api/v1/track/...`. In Caddy ist `/api*`
öffentlich durchgereicht — deshalb ist die Dashboard-Route selbst per Basic-Auth
geschützt (Passwort aus Env, Default nur lokal nutzbar).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import PageviewModel, WaitlistEntryModel

logger = logging.getLogger("sprossa.track")
router = APIRouter(tags=["tracking"])


# ─── Basic-Auth für das interne Dashboard ────────────────────────────────

def _dashboard_credentials() -> tuple[str, str]:
    user = os.getenv("DASHBOARD_USER", "sprossa")
    password = os.getenv("DASHBOARD_PASSWORD", "")
    return user, password


def _check_auth(request: Request) -> bool:
    user, password = _dashboard_credentials()
    if not password:
        # Kein Passwort gesetzt → Dashboard gesperrt (fail closed).
        return False
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
        got_user, got_password = decoded.split(":", 1)
    except Exception:
        return False
    return hmac.compare_digest(got_user, user) and hmac.compare_digest(got_password, password)


def require_dashboard_auth(request: Request) -> None:
    if not _check_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dashboard-Zugang nur intern.",
            headers={"WWW-Authenticate": 'Basic realm="Sprossa Dashboard"'},
        )


# ─── Pageview-Eingang ────────────────────────────────────────────────────

class PageviewIn(BaseModel):
    path: Optional[str] = "/"
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    device: Optional[str] = None


def _session_hash(ip: str, user_agent: str) -> str:
    """Täglich wechselnder, nicht rückführbarer Besucher-Hash."""
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    raw = f"{ip}|{user_agent}|{day}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


@router.post("/track/pageview", status_code=204)
async def track_pageview(body: PageviewIn, request: Request, db: AsyncSession = Depends(get_db)):
    """Nimmt einen Seitenaufruf entgegen. Antwortet immer 204 (kein Info-Leak)."""
    try:
        # IP aus Proxy-Header (Caddy setzt X-Forwarded-For) – nur für den Hash,
        # wird nicht gespeichert.
        ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
              or (request.client.host if request.client else ""))
        ua = request.headers.get("user-agent", "")[:200]
        session_hash = _session_hash(ip, ua) if ip else None

        # Crawler/Bots nicht mitzählen (grob, reicht für ein internes Dashboard).
        if ua.lower().startswith(("bot", "crawler", "spider")) or "bot/" in ua.lower():
            return None

        db.add(PageviewModel(
            created_at=datetime.now(UTC),
            path=(body.path or "/")[:500],
            referrer=(body.referrer or "")[:500] or None,
            utm_source=(body.utm_source or "")[:100] or None,
            utm_medium=(body.utm_medium or "")[:100] or None,
            utm_campaign=(body.utm_campaign or "")[:100] or None,
            utm_content=(body.utm_content or "")[:100] or None,
            session_hash=session_hash,
            device=(body.device or "")[:20] or None,
        ))
        await db.commit()
    except Exception as exc:  # Tracking darf nie die Seite stören
        logger.warning("pageview nicht gespeichert: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass
    return None


# ─── Dashboard-Daten ─────────────────────────────────────────────────────

@router.get("/track/dashboard", dependencies=[Depends(require_dashboard_auth)])
async def dashboard_data(days: int = 14, db: AsyncSession = Depends(get_db)):
    """Aggregierte Kennzahlen für das interne Dashboard."""
    since = datetime.now(UTC) - timedelta(days=max(1, min(days, 365)))

    # Gesamtzahl + eindeutige Besucher im Zeitraum
    total = await db.scalar(
        select(func.count()).select_from(PageviewModel).where(PageviewModel.created_at >= since)
    ) or 0
    uniques = await db.scalar(
        select(func.count(func.distinct(PageviewModel.session_hash)))
        .where(PageviewModel.created_at >= since)
    ) or 0

    # Nach Quelle (utm_source), leerer Wert = organisch/direkt
    by_source = (await db.execute(
        select(
            func.coalesce(PageviewModel.utm_source, "(direkt)").label("source"),
            func.count().label("visits"),
            func.count(func.distinct(PageviewModel.session_hash)).label("uniques"),
        )
        .where(PageviewModel.created_at >= since)
        .group_by("source")
        .order_by(func.count().desc())
    )).all()

    # Nach Kampagne
    by_campaign = (await db.execute(
        select(
            func.coalesce(PageviewModel.utm_campaign, "(keine)").label("campaign"),
            func.count().label("visits"),
        )
        .where(PageviewModel.created_at >= since)
        .group_by("campaign")
        .order_by(func.count().desc())
    )).all()

    # Nach Tag
    by_day = (await db.execute(
        select(
            func.date_trunc("day", PageviewModel.created_at).label("day"),
            func.count().label("visits"),
            func.count(func.distinct(PageviewModel.session_hash)).label("uniques"),
        )
        .where(PageviewModel.created_at >= since)
        .group_by("day")
        .order_by("day")
    )).all()

    # Top-Referrer (nur externe)
    by_referrer = (await db.execute(
        select(PageviewModel.referrer, func.count().label("visits"))
        .where(PageviewModel.created_at >= since)
        .where(PageviewModel.referrer.isnot(None))
        .where(PageviewModel.referrer != "")
        .group_by(PageviewModel.referrer)
        .order_by(func.count().desc())
        .limit(10)
    )).all()

    # Geräte
    by_device = (await db.execute(
        select(func.coalesce(PageviewModel.device, "?").label("device"), func.count().label("visits"))
        .where(PageviewModel.created_at >= since)
        .group_by("device")
        .order_by(func.count().desc())
    )).all()

    # Waitlist gesamt + nach Quelle
    wl_total = await db.scalar(select(func.count()).select_from(WaitlistEntryModel)) or 0
    wl_confirmed = await db.scalar(
        select(func.count()).select_from(WaitlistEntryModel)
        .where(WaitlistEntryModel.confirmed_at.isnot(None))
    ) or 0
    wl_by_source = (await db.execute(
        select(
            func.coalesce(WaitlistEntryModel.source, "(unbekannt)").label("source"),
            func.count().label("entries"),
        )
        .group_by("source")
        .order_by(func.count().desc())
    )).all()

    # Letzte Einträge (E-Mail maskiert)
    recent = (await db.execute(
        select(WaitlistEntryModel)
        .order_by(WaitlistEntryModel.created_at.desc())
        .limit(15)
    )).scalars().all()

    def mask(email: str) -> str:
        local, _, domain = email.partition("@")
        return f"{local[:2]}***@{domain}" if domain else "***"

    return {
        "range_days": days,
        "generated_at": datetime.now(UTC).isoformat(),
        "traffic": {
            "visits": total,
            "unique_visitors": uniques,
        },
        "by_source": [
            {"source": r.source, "visits": r.visits, "unique_visitors": r.uniques} for r in by_source
        ],
        "by_campaign": [{"campaign": r.campaign, "visits": r.visits} for r in by_campaign],
        "by_day": [
            {"day": r.day.date().isoformat(), "visits": r.visits, "unique_visitors": r.uniques}
            for r in by_day
        ],
        "top_referrers": [{"referrer": r.referrer, "visits": r.visits} for r in by_referrer],
        "by_device": [{"device": r.device, "visits": r.visits} for r in by_device],
        "waitlist": {
            "total": wl_total,
            "confirmed": wl_confirmed,
            "by_source": [{"source": r.source, "entries": r.entries} for r in wl_by_source],
            "recent": [
                {
                    "email": mask(e.email),
                    "source": e.source,
                    "utm_campaign": e.utm_campaign,
                    "confirmed": e.confirmed_at is not None,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in recent
            ],
        },
    }


# ─── Dashboard-Ansicht (HTML, intern) ────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Sprossa · Traffic-Dashboard</title>
<style>
  :root {
    --green: #3A7D44; --green-dark: #2C5F35; --green-soft: #E8F0E9;
    --terra: #D96B4A; --ink: #26302B; --paper: #FAF6EF; --line: #DED8CC;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: "Nunito", -apple-system, "Segoe UI", sans-serif;
    padding: 32px 24px 64px;
  }
  h1 { font-family: Georgia, "Times New Roman", serif; font-size: 30px; margin: 0 0 4px; color: var(--green-dark); }
  .sub { color: #6B7A70; font-size: 14px; margin-bottom: 28px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .card {
    background: #fff; border: 1px solid var(--line); border-radius: 14px;
    padding: 20px 22px;
  }
  .card .label { font-size: 12px; text-transform: uppercase; letter-spacing: 1.2px; color: #6B7A70; font-weight: 800; }
  .card .value { font-family: Georgia, serif; font-size: 34px; font-weight: 700; color: var(--green-dark); margin-top: 6px; }
  .card .hint { font-size: 12px; color: #8A968D; margin-top: 2px; }
  .panel { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 22px; margin-bottom: 20px; }
  .panel h2 { font-size: 15px; text-transform: uppercase; letter-spacing: 1.2px; color: var(--green); margin: 0 0 14px; font-weight: 800; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #6B7A70; padding: 8px 10px; border-bottom: 2px solid var(--line); }
  td { padding: 9px 10px; border-bottom: 1px solid #EFEBE3; }
  tr:last-child td { border-bottom: none; }
  .bar { height: 8px; background: var(--green-soft); border-radius: 4px; overflow: hidden; min-width: 60px; }
  .bar > span { display: block; height: 100%; background: var(--green); border-radius: 4px; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .empty { color: #9AA69C; font-style: italic; padding: 12px 0; }
  .ok { color: var(--green); font-weight: 700; }
  .pending { color: var(--terra); font-weight: 700; }
  footer { color: #9AA69C; font-size: 12px; margin-top: 28px; }
</style>
</head>
<body>
<h1>Traffic-Dashboard</h1>
<div class="sub">sprossa.de · nur intern · Datenquelle: eigene Pageview-Tabelle (keine IP, kein Cookie)</div>

<div class="cards" id="cards"></div>

<div class="panel">
  <h2>Zugriffe nach Quelle</h2>
  <div id="sources"></div>
</div>

<div class="panel">
  <h2>Zugriffe nach Tag</h2>
  <div id="days"></div>
</div>

<div class="panel">
  <h2>Waitlist</h2>
  <div id="waitlist"></div>
</div>

<div class="panel">
  <h2>Top-Referrer</h2>
  <div id="referrers"></div>
</div>

<footer>Auto-Refresh alle 60 s · Zeitraum: letzte 14 Tage</footer>

<script>
const fmt = (n) => new Intl.NumberFormat('de-DE').format(n);

function table(rows, cols, render) {
  if (!rows || !rows.length) return '<div class="empty">Noch keine Daten – sobald der Pin Traffic bringt, erscheint es hier.</div>';
  const head = cols.map(c => `<th>${c}</th>`).join('');
  const body = rows.map(render).join('');
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

async function load() {
  const res = await fetch('/api/v1/track/dashboard?days=14');
  if (!res.ok) { document.body.innerHTML = '<p style="padding:40px">Nicht autorisiert oder Backend nicht erreichbar.</p>'; return; }
  const d = await res.json();

  document.getElementById('cards').innerHTML = `
    <div class="card"><div class="label">Zugriffe</div><div class="value">${fmt(d.traffic.visits)}</div><div class="hint">letzte ${d.range_days} Tage</div></div>
    <div class="card"><div class="label">Eindeutige Besucher</div><div class="value">${fmt(d.traffic.unique_visitors)}</div><div class="hint">täglich gehashter Zähler</div></div>
    <div class="card"><div class="label">Waitlist gesamt</div><div class="value">${fmt(d.waitlist.total)}</div><div class="hint">${fmt(d.waitlist.confirmed)} bestätigt</div></div>
    <div class="card"><div class="label">Conversion</div><div class="value">${d.traffic.unique_visitors ? ((d.waitlist.total / d.traffic.unique_visitors) * 100).toFixed(1) : '0'} %</div><div class="hint">Waitlist / Besucher</div></div>
  `;

  const maxV = Math.max(...(d.by_source.map(s => s.visits) || [1]), 1);
  document.getElementById('sources').innerHTML = table(d.by_source, ['Quelle','Zugriffe','Besucher',''], r => `
    <tr><td><strong>${r.source}</strong></td><td class="num">${fmt(r.visits)}</td><td class="num">${fmt(r.unique_visitors)}</td>
    <td><div class="bar"><span style="width:${(r.visits/maxV*100).toFixed(0)}%"></span></div></td></tr>`);

  const maxD = Math.max(...(d.by_day.map(x => x.visits) || [1]), 1);
  document.getElementById('days').innerHTML = table(d.by_day, ['Tag','Zugriffe','Besucher',''], r => `
    <tr><td>${r.day}</td><td class="num">${fmt(r.visits)}</td><td class="num">${fmt(r.unique_visitors)}</td>
    <td><div class="bar"><span style="width:${(r.visits/maxD*100).toFixed(0)}%"></span></div></td></tr>`);

  document.getElementById('waitlist').innerHTML =
    table(d.waitlist.by_source, ['Quelle','Einträge',''], r => `
      <tr><td><strong>${r.source}</strong></td><td class="num">${fmt(r.entries)}</td><td></td></tr>`) +
    '<h2 style="margin-top:22px">Letzte Einträge</h2>' +
    table(d.waitlist.recent, ['E-Mail','Quelle','Kampagne','Status','Datum'], r => `
      <tr><td>${r.email}</td><td>${r.source || '–'}</td><td>${r.utm_campaign || '–'}</td>
      <td class="${r.confirmed ? 'ok' : 'pending'}">${r.confirmed ? 'bestätigt' : 'offen'}</td>
      <td>${r.created_at ? new Date(r.created_at).toLocaleString('de-DE') : '–'}</td></tr>`);

  document.getElementById('referrers').innerHTML =
    table(d.top_referrers, ['Referrer','Zugriffe'], r => `<tr><td>${r.referrer}</td><td class="num">${fmt(r.visits)}</td></tr>`);
}

load();
setInterval(load, 60000);
</script>
</body>
</html>"""


@router.get("/track/dashboard/view", response_class=HTMLResponse, dependencies=[Depends(require_dashboard_auth)])
async def dashboard_view():
    return HTMLResponse(DASHBOARD_HTML)
