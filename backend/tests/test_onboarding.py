#!/usr/bin/env python3
"""E2E-Onboarding-Test: Simuliert den kompletten User-Flow gegen localhost:8100.

Verwendung:
    cd backend && python3 tests/test_onboarding.py

Erwartet:
    - Eine laufende API-Instanz auf localhost:8100 (mit Postgres)
    - Kein Auth-Token erforderlich (erstellt Demo-User)

Flow:
    1. User registriert sich (POST /auth/register)
    2. Loggt ein (POST /auth/login)
    3. Erstellt Household (POST /households)
    4. Fügt Members hinzu (POST /households/{id}/members)
    5. Ruft Rezepte ab (GET /recipes)
    6. Generiert Plan (POST /plans/generate)
    7. Ruft Einkaufsliste ab (GET /grocery-lists)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
import uuid
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


BASE = "http://localhost:8100/api/v1"


def _req(method, path, body=None, token=None, quiet=False):
    """Führt einen HTTP-Request aus und gibt (status, data) zurück."""
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode()
            try:
                return status, json.loads(raw)
            except json.JSONDecodeError:
                return status, raw
    except HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"detail": raw}
    except Exception as e:
        return 0, {"error": str(e)}


def print_step(step: int, label: str):
    print(f"\n{'='*60}")
    print(f"  Schritt {step}: {label}")
    print(f"{'='*60}")


def assert_ok(status, data, step_name):
    assert 200 <= status < 300, (
        f"❌ {step_name} fehlgeschlagen: HTTP {status} – {data}"
    )
    print(f"  ✅ {step_name} – Status {status}")


def main():
    print(f"\n{'='*60}")
    print(f"  Sprossa E2E Onboarding-Test")
    print(f"  Endpoint: {BASE}")
    print(f"  Zeit: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Prüfe Health
    status, data = _req("GET", "/../health")
    if status != 200:
        print(f"❌ API nicht erreichbar auf {BASE}/../health (HTTP {status})")
        print(f"  Starte zuerst die API: docker compose up -d")
        sys.exit(1)
    print(f"  ✅ API läuft: {data}\n")

    unique_suffix = uuid.uuid4().hex[:8]
    user_email = f"e2e-{unique_suffix}@sprossa-test.de"
    user_password = "E2ETestPass!123"
    token = None
    household_id = None

    # ── 1. Registrierung ──────────────────────────────────────────────────
    print_step(1, "User registrieren")
    status, data = _req("POST", "/auth/register", {
        "email": user_email,
        "password": user_password,
        "display_name": "E2E-Test-Familie",
    })
    assert_ok(status, data, "Registrierung")
    token = data.get("access_token")
    assert token, f"Kein Token erhalten: {data}"
    print(f"  🆔 User: {user_email}")
    print(f"  🔑 Token: {token[:20]}...")

    # ── 2. Login ──────────────────────────────────────────────────────────
    print_step(2, "Login")
    status, data = _req("POST", "/auth/login", {
        "email": user_email,
        "password": user_password,
    })
    assert_ok(status, data, "Login")
    token = data.get("access_token", token)
    print(f"  🔑 Token erneuert: OK")

    # ── 3. Household erstellen ────────────────────────────────────────────
    print_step(3, "Household erstellen")
    status, data = _req("POST", "/households", {
        "name": f"E2E-Haushalt-{unique_suffix}",
        "dietary_profile": {"preferences": ["familie"]},
    }, token=token)
    assert_ok(status, data, "Household-Erstellung")
    household_id = data.get("id")
    assert household_id, f"Keine household_id: {data}"
    print(f"  🏠 Household ID: {household_id}")
    print(f"  📛 Name: {data.get('name')}")

    # ── 4. Members hinzufügen ─────────────────────────────────────────────
    print_step(4, "Members hinzufügen")
    members = [
        {"name": "Eltern", "age": 35},
        {"name": "Kind 1", "age": 8},
        {"name": "Kind 2", "age": 5},
    ]
    created_members = []
    for m in members:
        status, data = _req("POST", f"/households/{household_id}/members", m, token=token)
        assert_ok(status, data, f"Member '{m['name']}' anlegen")
        created_members.append(data)
        print(f"    👤 {data.get('name')} – ID: {data.get('id')}")

    # ── 5. Rezepte abrufen ────────────────────────────────────────────────
    print_step(5, "Rezepte abrufen")
    status, data = _req("GET", "/recipes", token=token)
    assert_ok(status, data, "Rezepte abrufen")
    recipes = data if isinstance(data, list) else []
    print(f"  📖 {len(recipes)} Rezepte gefunden")

    if len(recipes) == 0:
        print("  ⚠ Keine Rezepte vorhanden (Seed erforderlich)")
        print("  Führe aus: cd backend && python seed.py")
    else:
        print(f"  → Erstes Rezept: {recipes[0].get('title', '?')}")

    # ── 6. Plan generieren ────────────────────────────────────────────────
    print_step(6, "Plan generieren")
    if len(recipes) > 0:
        status, data = _req("POST", "/plans/generate", {
            "month": 10,
            "year": 2026,
            "focus_tags": ["schnell", "familie"],
        }, token=token)
        assert_ok(status, data, "Plan-Generierung")
        plan_id = data.get("plan_id")
        print(f"  📅 Plan ID: {plan_id}")
        print(f"  📆 {data.get('month')}/{data.get('year')}")
        print(f"  📊 {data.get('weeks')} Wochen, {data.get('meal_slots_total')} Mahlzeiten")

        # Weekly-Pläne abrufen
        if plan_id:
            status, weeks_data = _req("GET", f"/plans/{plan_id}/weeks", token=token)
            if status == 200 and isinstance(weeks_data, list):
                print(f"  📋 {len(weeks_data)} Wochenpläne geladen")
                for wp in weeks_data[:2]:  # Erste 2 Wochen anzeigen
                    slots = wp.get("meal_slots", [])
                    print(f"    Woche {wp.get('week_number')}: {len(slots)} Slots")
    else:
        print("  ⏭ Übersprungen (keine Rezepte)")

    # ── 7. Einkaufsliste abrufen ──────────────────────────────────────────
    print_step(7, "Einkaufsliste abrufen")
    status, data = _req("GET", "/grocery-lists", token=token)
    assert_ok(status, data, "Einkaufslisten abrufen")
    lists = data if isinstance(data, list) else []
    print(f"  🛒 {len(lists)} Einkaufslisten gefunden")
    if lists:
        for l in lists[:3]:
            items = l.get("items", [])
            print(f"    Liste {l.get('id', '?')[:8]}: {len(items)} Items")

    # ── Zusammenfassung ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  ✅ E2E-Test erfolgreich!")
    print(f"{'='*60}")
    print(f"\n  Flow: Register → Login → Household → Members → Recipes → Plan → Grocery")
    print(f"  User: {user_email}")
    print(f"  Passwort: {user_password}")
    print(f"  Household: {household_id}")
    print(f"\n  Bereinigung: Lösche den User manuell via DB oder ignoriere ihn.")
    print(f"\n{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())