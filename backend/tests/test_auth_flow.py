#!/usr/bin/env python3
"""Integrationstest: Auth-Flow gegen die laufende API (localhost:8100).

Testet den vollständigen Auth-Zyklus:
  1. POST /api/v1/auth/register – User registrieren
  2. POST /api/v1/auth/login   – Token abrufen
  3. GET  /api/v1/auth/me       – Eigenen User auslesen

Lauffähig mit:
    source .venv/bin/activate && python3 -m pytest tests/test_auth_flow.py -v

Oder direkt:
    source .venv/bin/activate && python3 tests/test_auth_flow.py
"""
import sys
import os
import unittest
from uuid import uuid4

import httpx

API_BASE = os.environ.get("MM_API_BASE", "http://localhost:8100/api/v1")


class TestAuthFlow(unittest.TestCase):
    """Lebt gegen die echte Postgres-Datenbank (Test-Instanz auf :8100)."""

    @classmethod
    def setUpClass(cls):
        """Prüft ob die API erreichbar ist."""
        try:
            r = httpx.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=3)
            cls.api_ok = r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            cls.api_ok = False

        if not cls.api_ok:
            raise RuntimeError(
                f"API unter {API_BASE} nicht erreichbar. "
                f"Starte die Test-Instanz mit: "
                f"cd backend && source .venv/bin/activate && "
                f"MM_DEBUG=false uvicorn app.main:app --port 8100 &"
            )

    def _unique_email(self) -> str:
        """Erzeugt eine einmalige E-Mail für jeden Testlauf."""
        tag = uuid4().hex[:8]
        return f"auth-test-{tag}@sprossa.de"

    # ── Tests ─────────────────────────────────────────────────────────────

    def test_01_register_success(self):
        """Registriert einen neuen User → 201 + access_token."""
        email = self._unique_email()
        payload = {
            "email": email,
            "password": "Test1234!",
            "display_name": "Auth Test User",
        }
        r = httpx.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
        self.assertEqual(
            r.status_code, 201,
            f"Register sollte 201 sein, war {r.status_code}: {r.text}",
        )
        body = r.json()
        self.assertIn("access_token", body, "Token im Response erwartet")
        self.assertEqual(body["token_type"], "bearer")
        # Token-Format prüfen (3 Segmente)
        parts = body["access_token"].split(".")
        self.assertEqual(len(parts), 3, "JWT sollte 3 Segmente haben")

    def test_02_register_duplicate(self):
        """Doppelte E-Mail → 409 Conflict."""
        email = self._unique_email()
        payload = {
            "email": email,
            "password": "Test1234!",
            "display_name": "Dupe Test",
        }
        # Erste Registrierung
        r1 = httpx.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
        self.assertEqual(r1.status_code, 201)

        # Zweite Registrierung (gleiche E-Mail)
        r2 = httpx.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
        self.assertEqual(
            r2.status_code, 409,
            f"Doppelte Registrierung sollte 409 sein, war {r2.status_code}: {r2.text}",
        )
        self.assertIn("Email already registered", r2.text)

    def test_03_login_success(self):
        """Login mit gültigen Credentials → 200 + Token."""
        email = self._unique_email()
        pw = "MeinPasswort!99"
        # Vorher registrieren
        reg = httpx.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": pw, "display_name": "Login Test"},
            timeout=10,
        )
        self.assertEqual(reg.status_code, 201)

        # Login
        r = httpx.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": pw},
            timeout=10,
        )
        self.assertEqual(
            r.status_code, 200,
            f"Login sollte 200 sein, war {r.status_code}: {r.text}",
        )
        body = r.json()
        self.assertIn("access_token", body)
        parts = body["access_token"].split(".")
        self.assertEqual(len(parts), 3, "JWT sollte 3 Segmente haben")

    def test_04_login_wrong_password(self):
        """Login mit falschem Passwort → 401."""
        email = self._unique_email()
        # Registrieren
        httpx.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": "RichtigesPW99", "display_name": "Fail Test"},
            timeout=10,
        )
        # Falsches PW
        r = httpx.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": "falschesPW"},
            timeout=10,
        )
        self.assertEqual(
            r.status_code, 401,
            f"Falsches PW sollte 401 sein, war {r.status_code}",
        )

    def test_05_login_nonexistent_user(self):
        """Login mit nicht-existenter E-Mail → 401."""
        r = httpx.post(
            f"{API_BASE}/auth/login",
            json={"email": "nobody@nirgendwo.de", "password": "irgendwas"},
            timeout=10,
        )
        self.assertEqual(r.status_code, 401)

    def test_06_me_with_valid_token(self):
        """GET /auth/me mit gültigem Token → 200 + User-Daten."""
        email = self._unique_email()
        # Registrieren
        reg = httpx.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": "TokenTest77", "display_name": "Me Test"},
            timeout=10,
        )
        token = reg.json()["access_token"]

        # Me aufrufen
        r = httpx.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        self.assertEqual(
            r.status_code, 200,
            f"/me sollte 200 sein, war {r.status_code}: {r.text}",
        )
        body = r.json()
        self.assertEqual(body["email"], email)
        self.assertEqual(body["display_name"], "Me Test")
        self.assertIn("id", body)
        self.assertIn("created_at", body)
        self.assertTrue(body["is_active"])

    def test_07_me_without_token(self):
        """GET /auth/me ohne Token → 401."""
        r = httpx.get(f"{API_BASE}/auth/me", timeout=10)
        self.assertEqual(r.status_code, 401)

    def test_08_me_with_invalid_token(self):
        """GET /auth/me mit ungültigem Token → 401."""
        r = httpx.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": "Bearer dies.ist.kein.gueltiger.token"},
            timeout=10,
        )
        self.assertEqual(r.status_code, 401)

    def test_09_full_flow(self):
        """Kompletter Flow: Registrieren → Login → Me."""
        email = self._unique_email()

        # 1. Register
        r1 = httpx.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": "FullFlow99!", "display_name": "Flow Test"},
            timeout=10,
        )
        self.assertEqual(r1.status_code, 201)
        register_token = r1.json()["access_token"]

        # 2. Login
        r2 = httpx.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": "FullFlow99!"},
            timeout=10,
        )
        self.assertEqual(r2.status_code, 200)
        login_token = r2.json()["access_token"]

        # 3. Me (mit Login-Token)
        r3 = httpx.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {login_token}"},
            timeout=10,
        )
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["email"], email)

        # 4. Me (mit Register-Token – sollte auch funktionieren, gleicher User)
        r4 = httpx.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {register_token}"},
            timeout=10,
        )
        self.assertEqual(r4.status_code, 200)
        # Beide Tokens gehören demselben User
        self.assertEqual(r3.json()["id"], r4.json()["id"],
                         "Register- und Login-Token sollten denselben User referenzieren")


if __name__ == "__main__":
    unittest.main(verbosity=2)