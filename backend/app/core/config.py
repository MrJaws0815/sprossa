"""App-Konfiguration via Umgebungsvariablen"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Monatsmenue API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://monatsmenue:monatsmenue@localhost:5432/monatsmenue"
    database_url_sync: str = "postgresql://monatsmenue:monatsmenue@localhost:5432/monatsmenue"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # Stripe
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # SMTP (Strato)
    smtp_host: str = "smtp.strato.de"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "hallo@sprossa.de"

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)

    class Config:
        env_file = ".env"
        env_prefix = "MM_"


settings = Settings()