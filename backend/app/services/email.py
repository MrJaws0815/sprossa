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