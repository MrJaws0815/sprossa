"""E-Mail-Versand für Sprossa (Double-Opt-in).

Unterstützt zwei Modi:
1. **DEV/Log-Modus** (Default): Gibt die E-Mail nur auf der Konsole aus.
2. **SMTP-Modus** (Produktion): Sendet über Strato SMTP, sobald MM_SMTP_* gesetzt sind.

Konfiguration via .env / Umgebungsvariablen:
  MM_SMTP_HOST=smtp.strato.de
  MM_SMTP_PORT=587
  MM_SMTP_USER=hallo@sprossa.de
  MM_SMTP_PASSWORD=***
  MM_SMTP_FROM=hallo@sprossa.de
  MM_SMTP_FROM_NAME=Sprossa
"""
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger("sprossa.mail")
logger.setLevel(logging.INFO)

# ─── Konfiguration aus Umgebungsvariablen ────────────────────────────────

SMTP_HOST: Optional[str] = os.getenv("MM_SMTP_HOST")
SMTP_PORT: int = int(os.getenv("MM_SMTP_PORT", "587"))
SMTP_USER: Optional[str] = os.getenv("MM_SMTP_USER") or os.getenv("MM_SMTP_USERNAME")
SMTP_PASSWORD: Optional[str] = os.getenv("MM_SMTP_PASSWORD")
SMTP_FROM: str = os.getenv("MM_SMTP_FROM", "hallo@sprossa.de")
SMTP_FROM_NAME: str = os.getenv("MM_SMTP_FROM_NAME", "Sprossa")
SMTP_USE_TLS: bool = os.getenv("MM_SMTP_USE_TLS", "true").lower() == "true"


def is_smtp_configured() -> bool:
    """Prüft, ob SMTP-Zugangsdaten vorhanden sind (Produktionsmodus)."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


# ─── E-Mail-Bau ──────────────────────────────────────────────────────────

def build_confirmation_email(to_email: str, token: str, base_url: str) -> tuple[str, str]:
    """Baut HTML + Plaintext für die Double-Opt-in-Bestätigungsmail.

    Returns: (html_body, plaintext_body)
    """
    confirm_url = f"{base_url.rstrip('/')}/api/v1/waitlist/confirm?token={token}"
    unsubscribe_url = f"{base_url.rstrip('/')}/api/v1/waitlist/unsubscribe?token={token}"

    html = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Nunito','Segoe UI',sans-serif;background:#FAF6EF;padding:32px 0;">
<div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:16px;padding:32px 40px;">
<div style="text-align:center;margin-bottom:24px;">
<span style="display:inline-block;width:48px;height:48px;border-radius:12px;background:#3A7D44;color:#fff;font-size:24px;line-height:48px;text-align:center;">🌱</span>
</div>
<h1 style="color:#26302B;font-size:24px;margin-bottom:16px;">Fast geschafft! 🌱</h1>
<p style="color:#68736C;font-size:16px;line-height:1.6;">Hallo,<br><br>
du hast dich gerade für die kostenlose Beta von <strong>Sprossa</strong> angemeldet.
Bitte bestätige deine E-Mail-Adresse, um die Anmeldung abzuschließen:</p>
<div style="text-align:center;margin:24px 0;">
<a href="{confirm_url}"
   style="display:inline-block;padding:16px 36px;background:#3A7D44;color:#ffffff;font-size:18px;font-weight:bold;border-radius:14px;text-decoration:none;">
  Jetzt bestätigen
</a>
</div>
<p style="color:#68736C;font-size:14px;line-height:1.5;">
Falls du dich nicht angemeldet hast, kannst du diese E-Mail einfach ignorieren.<br>
Deine Daten werden gemäß unserer <a href="{base_url}/datenschutz" style="color:#3A7D44;">Datenschutzerklärung</a> verarbeitet.</p>
<hr style="border:none;border-top:1px solid rgba(38,48,43,0.1);margin:24px 0;">
<p style="color:#68736C;font-size:12px;">
  🌱 Sprossa · euer Monat, klug geplant<br>
  <a href="{unsubscribe_url}" style="color:#3A7D44;">Anmeldung widerrufen</a>
</p>
</div>
</body>
</html>"""

    text = f"""Fast geschafft! 🌱

Hallo,

du hast dich gerade für die kostenlose Beta von Sprossa angemeldet.
Bitte bestätige deine E-Mail-Adresse, um die Anmeldung abzuschließen:

{confirm_url}

Falls du dich nicht angemeldet hast, kannst du diese E-Mail einfach ignorieren.
Deine Daten werden gemäß unserer Datenschutzerklärung verarbeitet ({base_url}/datenschutz).

---
🌱 Sprossa · euer Monat, klug geplant
Widerruf: {unsubscribe_url}
"""
    return html, text


# ─── Versand ─────────────────────────────────────────────────────────────

async def send_confirmation_email(to_email: str, token: str, base_url: str) -> bool:
    """Sendet die DOI-Bestätigungsmail oder loggt sie im Dev-Modus.

    Returns: True bei Erfolg (oder Dev-Modus), False bei Fehler.
    """
    html, text = build_confirmation_email(to_email, token, base_url)

    if not is_smtp_configured():
        # ── DEV-Modus: Loggen ─────────────────────────────────
        logger.info("=" * 60)
        logger.info(f"📧 [DOI-MAIL] An: {to_email}")
        logger.info(f"🔗 Bestätigungslink: {base_url.rstrip('/')}/api/v1/waitlist/confirm?token={token}")
        logger.info(f"📝 HTML: {len(html)} Zeichen, Plaintext: {len(text)} Zeichen")
        logger.info("⚠️  SMTP nicht konfiguriert – E-Mail NUR geloggt.")
        logger.info("=" * 60)
        return True  # Im Dev-Modus immer Erfolg

    # ── Produktion: SMTP-Versand ─────────────────────────────
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Fast geschafft! Bitte bestätige deine Anmeldung bei Sprossa"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
        msg["To"] = to_email
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            logger.info("EHLO abgeschlossen")
            if SMTP_USE_TLS:
                server.starttls(context=ctx)
                server.ehlo()
                logger.info("STARTTLS abgeschlossen")
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info("SMTP-Login erfolgreich")
            server.send_message(msg)
            logger.info("Mail gesendet")

        logger.info(f"✅ DOI-Mail gesendet an {to_email}")
        return True

    except Exception as e:
        logger.error(f"❌ DOI-Mail FEHLER an {to_email}: {e}")
        return False