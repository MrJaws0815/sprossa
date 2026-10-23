"""SMTP-Versand für Bestätigungs- und Transaktionsmails (Strato)."""
import logging
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

# Explizite Konfiguration, damit Versand-Erfolg/Fehler in den Uvicorn-Docker-Logs sichtbar sind
# (Uvicorn bindet unkonfigurierte Modul-Logger nicht standardmäßig an).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _build_confirmation_email(to_email: str, name: str | None) -> EmailMessage:
    """Baut die Waitlist-Bestätigungsmail (Plaintext + HTML)."""
    anrede = f"Hi {name.strip()}," if (name and name.strip()) else "Hi,"
    subject = "Du bist auf der Sprossa-Warteliste! 🌱"

    # URL für späteren Verweis (falls sie je gesetzt wird)
    text = f"""\
{anrede}

Danke für deine Anmeldung zur Sprossa-Beta-Warteliste!

Du gehörst zu den ersten, die erfahren, wenn Sprossa live geht. Bis dahin
bauen wir an einem Ernährungsplaner, der dir für einen ganzen Monat
komplette, personalisierte Essenspläne mit Rezepten und optimierter
Einkaufsliste liefert.

Wir melden uns bei dir, sobald etwas los ist.

Bis bald,
dein Sprossa-Team
"""

    html = f"""\
<!doctype html>
<html>
  <body style="font-family:Arial,Helvetica,sans-serif;color:#1f2d22;max-width:560px;margin:0 auto;padding:24px;">
    <h2 style="color:#2e7d32;">Sprossa 🌱</h2>
    <p>{anrede}</p>
    <p>Danke für deine Anmeldung zur <strong>Beta-Warteliste</strong>!</p>
    <p>Du gehörst zu den ersten, die erfahren, wenn <strong>Sprossa</strong> live geht.
       Bis dahin bauen wir an einem Ernährungsplaner, der dir für einen ganzen Monat
       komplette, personalisierte Essenspläne mit Rezepten und optimierter Einkaufsliste liefert.</p>
    <p>Wir melden uns bei dir, sobald etwas los ist.</p>
    <p style="margin-top:28px;">Bis bald,<br><strong>dein Sprossa-Team</strong></p>
    <p style="margin-top:32px;font-size:12px;color:#888;">
      <a href="https://sprossa.de" style="color:#2e7d32;">sprossa.de</a>
    </p>
  </body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Sprossa", "hallo@sprossa.de"))
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def send_confirmation_email(to_email: str, name: str | None = None) -> None:
    """Sendet die Bestätigungsmail über Strato SMTP. Synchron (for Threadpool)."""
    if not settings.smtp_enabled:
        logger.info("SMTP deaktiviert — Bestätigungsmail an %s übersprungen.", to_email)
        return

    msg = _build_confirmation_email(to_email, name)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.ehlo()
            if settings.smtp_use_tls:
                s.starttls()
                s.ehlo()
            s.login(settings.smtp_username, settings.smtp_password)
            s.send_message(msg)
        logger.info("Bestätigungsmail an %s versendet.", to_email)
    except Exception:
        # Nie den Signup scheitern lassen, nur weil Mail nicht rausging.
        logger.exception("Bestätigungsmail an %s fehlgeschlagen.", to_email)


# ─── Password-Reset-Mail ─────────────────────────────────────────────────


def send_password_reset_email(to_email: str, token: str) -> None:
    """Sendet eine Password-Reset-Mail oder loggt sie im Dev-Modus."""
    reset_url = f"https://sprossa.de/reset-password?token={token}"

    subject = "Passwort zurücksetzen – Sprossa 🌱"
    text = f"""\
Hi,

du hast ein Zurücksetzen deines Passworts für Sprossa angefordert.

Klicke auf den folgenden Link, um ein neues Passwort zu setzen:

{reset_url}

Dieser Link ist 1 Stunde gültig.

Falls du diese E-Mail nicht angefordert hast, kannst du sie einfach ignorieren.

Bis bald,
dein Sprossa-Team
"""

    html = f"""\
<!doctype html>
<html>
  <body style="font-family:Arial,Helvetica,sans-serif;color:#1f2d22;max-width:560px;margin:0 auto;padding:24px;">
    <h2 style="color:#3A7D44;">Sprossa 🌱</h2>
    <p>Hi,</p>
    <p>du hast ein Zurücksetzen deines Passworts für <strong>Sprossa</strong> angefordert.</p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{reset_url}"
         style="display:inline-block;padding:14px 32px;background:#3A7D44;color:#ffffff;font-size:16px;font-weight:bold;border-radius:12px;text-decoration:none;">
        Passwort zurücksetzen
      </a>
    </div>
    <p style="color:#68736C;font-size:14px;">Dieser Link ist <strong>1 Stunde</strong> gültig.</p>
    <p style="color:#68736C;font-size:14px;">Falls du diese E-Mail nicht angefordert hast, kannst du sie einfach ignorieren.</p>
    <p style="margin-top:28px;">Bis bald,<br><strong>dein Sprossa-Team</strong></p>
    <p style="margin-top:32px;font-size:12px;color:#888;">
      <a href="https://sprossa.de" style="color:#3A7D44;">sprossa.de</a>
    </p>
  </body>
</html>"""

    if not settings.smtp_enabled:
        logger.info("=" * 60)
        logger.info("📧 [PASSWORD-RESET] An: %s", to_email)
        logger.info("🔗 Reset-Link: %s", reset_url)
        logger.info("⚠️  SMTP nicht konfiguriert – E-Mail NUR geloggt.")
        logger.info("=" * 60)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Sprossa", "hallo@sprossa.de"))
    msg["To"] = to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.ehlo()
            if settings.smtp_use_tls:
                s.starttls()
                s.ehlo()
            s.login(settings.smtp_username, settings.smtp_password)
            s.send_message(msg)
        logger.info("Password-Reset-Mail an %s versendet.", to_email)
    except Exception:
        logger.exception("Password-Reset-Mail an %s fehlgeschlagen.", to_email)