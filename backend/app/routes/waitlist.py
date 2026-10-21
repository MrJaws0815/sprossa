"""Waitlist/Beta-Anmeldung API-Route (Postgres-persistent mit Double-Opt-in)."""
from datetime import datetime, UTC
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import WaitlistEntry
from app.repositories.postgres import PostgresWaitlistRepo, generate_token
from app.services.email_service import send_confirmation_email

logger = logging.getLogger("sprossa.waitlist")
router = APIRouter(tags=["waitlist"])


class WaitlistSignupRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    household_size: Optional[int] = None


class WaitlistSignupResponse(BaseModel):
    message: str
    email: str


@router.post("/waitlist/signup", response_model=WaitlistSignupResponse, status_code=201)
async def waitlist_signup(body: WaitlistSignupRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Trägt eine E-Mail in die Beta-Warteliste ein (Postgres-persistent + DOI)."""
    repo = PostgresWaitlistRepo(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        if existing.confirmed_at:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Diese E-Mail ist bereits auf der Warteliste.",
            )
        entry = existing
    else:
        entry = WaitlistEntry(
            email=body.email,
            name=body.name,
            household_size=body.household_size,
        )
        entry = await repo.save(entry)

    token = generate_token()
    await repo.set_confirmation_token(entry.id, token)

    base_url = str(request.base_url).rstrip("/")
    sent = await send_confirmation_email(body.email, token, base_url)

    if sent:
        msg = "Bitte bestätige deine E-Mail-Adresse. Wir haben dir eine Nachricht an {} gesendet.".format(body.email)
    else:
        msg = "Fast geschafft! Hier ist dein Bestätigungslink: {}. (E-Mail-Versand noch nicht aktiv.)".format(
            f"{base_url}/api/v1/waitlist/confirm?token={token}"
        )

    return WaitlistSignupResponse(message=msg, email=body.email)


@router.get("/waitlist/confirm")
async def waitlist_confirm(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Bestätigt eine E-Mail-Adresse via Double-Opt-in-Token."""
    repo = PostgresWaitlistRepo(db)
    entry = await repo.get_by_token(token)
    if entry is None:
        return _confirm_page("error", "Link ungültig",
            "Dieser Bestätigungslink ist ungültig oder wurde bereits verwendet.")

    if entry.confirmed_at:
        return _confirm_page("info", "Bereits bestätigt",
            "Deine E-Mail-Adresse wurde bereits bestätigt. Vielen Dank!")

    if entry.confirmation_sent_at:
        age = (datetime.now(UTC) - entry.confirmation_sent_at).total_seconds()
        if age > 48 * 3600:
            return _confirm_page("error", "Link abgelaufen",
                "Der Bestätigungslink ist leider abgelaufen (max. 48h gültig). Bitte melde dich erneut an.")

    client_ip = request.client.host if request.client else ""
    confirmed = await repo.confirm_by_token(token, client_ip)
    if confirmed is None:
        return _confirm_page("error", "Bestätigung fehlgeschlagen",
            "Die Bestätigung konnte nicht durchgeführt werden. Bitte versuche es später erneut.")

    return _confirm_page("success", "Anmeldung bestätigt! 🌱",
        "Deine E-Mail-Adresse wurde erfolgreich bestätigt. Wir halten dich auf dem Laufenden, sobald Sprossa startet!")


@router.get("/waitlist/unsubscribe")
async def waitlist_unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    """Widerruft die Einwilligung (Abmeldung)."""
    repo = PostgresWaitlistRepo(db)
    entry = await repo.get_by_token(token)
    if entry is None:
        return _confirm_page("info", "Bereits abgemeldet",
            "Du bist bereits von der Warteliste ausgetragen oder der Link ist ungültig.")

    from sqlalchemy import delete
    from uuid import UUID
    from app.models.database import WaitlistEntryModel
    q = delete(WaitlistEntryModel).where(WaitlistEntryModel.id == UUID(entry.id))
    await db.execute(q)
    await db.flush()

    return _confirm_page("success", "Erfolgreich abgemeldet",
        "Du wurdest von der Warteliste ausgetragen. Deine Daten wurden gelöscht.")


@router.get("/waitlist/count")
async def waitlist_count(db: AsyncSession = Depends(get_db)):
    """Gibt die Anzahl der bestätigten + gesamten Wartelisten-Einträge zurück."""
    repo = PostgresWaitlistRepo(db)
    return {"confirmed": await repo.count_confirmed(), "total": await repo.count()}


# ─── HTML-Bestätigungsseite ──────────────────────────────────────────────

def _confirm_page(status: str, title: str, detail: str) -> HTMLResponse:
    emoji = {"success": "✅", "error": "❌", "info": "ℹ️"}.get(status, "ℹ️")
    color = {"success": "#3A7D44", "error": "#C0392B", "info": "#26302B"}.get(status, "#26302B")
    html = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – Sprossa</title>
<style>body{{font-family:'Nunito','Segoe UI',sans-serif;background:#FAF6EF;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:24px;}}
.card{{max-width:520px;background:#fff;border-radius:20px;padding:40px;box-shadow:0 20px 40px rgba(38,48,43,0.08);text-align:center;}}
h1{{color:{color};font-size:28px;margin-bottom:16px;}}p{{color:#68736C;font-size:16px;line-height:1.6;}}
.btn{{display:inline-block;padding:14px 32px;background:#3A7D44;color:#fff;border-radius:14px;text-decoration:none;font-weight:bold;margin-top:24px;}}</style>
</head><body><div class="card"><div style="font-size:48px;margin-bottom:16px;">{emoji}</div>
<h1>{title}</h1><p>{detail}</p><a href="/" class="btn">Zur Startseite</a></div></body></html>"""
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")