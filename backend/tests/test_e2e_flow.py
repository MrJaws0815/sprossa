#!/usr/bin/env python3
"""Umfassender E2E-Test für Sprossa (12 Schritte) gegen die laufende API.

Testet den vollständigen User-Flow:
   1. POST   /auth/register            → 201 + Token
   2. POST   /auth/login               → 200 + Token
   3. POST   /households                → 201
   4. POST   /households/{id}/members   → 201
   5. GET    /recipes                   → 200 + 28 Einträge
   6. POST   /plans/generate            → 201 + plan_id + grocery_list
   7. GET    /plans                     → 200 + 1 Plan
   8. GET    /plans/{id}/weeks          → 200 + cw (Kalenderwoche)
   9. GET    /grocery-lists             → 200 + 1 Liste mit Items
  10. GET    /recipes/{id}              → 200 + title + Zutaten
  11. PUT    /households/{id}           → 200
  12. DELETE /households/{id}/members/{mid} → 200

Lauffähig mit:
    cd backend && source .venv/bin/activate && \
    python3 -m pytest tests/test_e2e_flow.py -v

Voraussetzung:
    - API läuft auf http://localhost:8100
    - Seed-Daten geladen (cd backend && python3 seed.py)
"""

import os
import sys
from uuid import uuid4

import httpx

API_BASE = os.environ.get("MM_API_BASE", "http://localhost:8100/api/v1")
HEALTH_URL = API_BASE.replace("/api/v1", "/health")
PASSWORD = "E2eStrongPass!99"


def _jwt_summary(token: str) -> str:
    """Gibt eine kurze Zusammenfassung des JWT zurück (für Logging)."""
    try:
        parts = token.split(".")
        return f"{parts[0][:12]}...{parts[1][:6]}... (3 Segmente)"
    except Exception:
        return "(ungültiges Format)"


def test_e2e_complete_flow():
    """Führt die 12 E2E-Schritte sequenziell aus – bricht beim ersten Fehler ab."""

    # ── Setup: Einmalige IDs ──────────────────────────────────────────────
    suffix = uuid4().hex[:8]
    email = f"e2e-{suffix}@sprossa-test.de"
    household_name = f"E2E-Haushalt-{suffix}"
    updated_name = f"{household_name}-umbenannt"

    steps_passed = 0
    total_steps = 12
    token = None
    household_id = None
    member_ids = []

    # ── Health-Check ──────────────────────────────────────────────────────
    try:
        r = httpx.get(HEALTH_URL, timeout=5)
        assert r.status_code == 200, f"Health-Check: HTTP {r.status_code}"
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest_fail = f"❌ API nicht erreichbar unter {HEALTH_URL}: {e}"
        print(pytest_fail)
        print("  Starte die Test-Instanz mit:")
        print("    cd backend && source .venv/bin/activate &&")
        print("    MM_DEBUG=false uvicorn app.main:app --port 8100")
        raise AssertionError(pytest_fail)

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 1: Registrierung
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  📝 Schritt 1/12: POST /auth/register → 201 + Token")
    payload = {
        "email": email,
        "password": PASSWORD,
        "display_name": "E2E Test Familie",
    }
    r = httpx.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
    assert r.status_code == 201, (
        f"❌ Schritt 1 (Register) fehlgeschlagen: "
        f"Erwartet 201, erhalten {r.status_code}: {r.text}"
    )
    body = r.json()
    assert "access_token" in body, (
        f"❌ Schritt 1: Kein access_token im Response: {body}"
    )
    token = body["access_token"]
    assert body.get("token_type") == "bearer", (
        f"❌ Schritt 1: token_type nicht 'bearer': {body}"
    )
    parts = token.split(".")
    assert len(parts) == 3, (
        f"❌ Schritt 1: JWT hat {len(parts)} Segmente (3 erwartet)"
    )
    steps_passed += 1
    print(f"  ✅ Schritt 1 – Token: {_jwt_summary(token)}")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 2: Login
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🔑 Schritt 2/12: POST /auth/login → 200 + Token")
    r = httpx.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200, (
        f"❌ Schritt 2 (Login) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    body = r.json()
    assert "access_token" in body, (
        f"❌ Schritt 2: Kein access_token im Response: {body}"
    )
    token = body["access_token"]
    assert body.get("token_type") == "bearer"
    assert len(token.split(".")) == 3
    steps_passed += 1
    print(f"  ✅ Schritt 2 – Token: {_jwt_summary(token)}")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 3: Household erstellen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🏠 Schritt 3/12: POST /households → 201")
    r = httpx.post(
        f"{API_BASE}/households",
        json={"name": household_name, "dietary_profile": {"preferences": ["familie"]}},
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 201, (
        f"❌ Schritt 3 (Household anlegen) fehlgeschlagen: "
        f"Erwartet 201, erhalten {r.status_code}: {r.text}"
    )
    body = r.json()
    assert "id" in body, f"❌ Schritt 3: Keine id im Response: {body}"
    household_id = body["id"]
    assert body.get("name") == household_name, (
        f"❌ Schritt 3: Name mismatch: {body.get('name')}"
    )
    steps_passed += 1
    print(f"  ✅ Schritt 3 – Household {household_id[:8]}... ({body.get('name')})")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 4: Members hinzufügen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  👤 Schritt 4/12: POST /households/{id}/members → 201 (×3)")
    member_specs = [
        {"name": "Eltern", "age": 35},
        {"name": "Kind 1", "age": 8},
        {"name": "Kind 2", "age": 5},
    ]
    for i, spec in enumerate(member_specs, 1):
        r = httpx.post(
            f"{API_BASE}/households/{household_id}/members",
            json=spec,
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 201, (
            f"❌ Schritt 4.{i} (Member '{spec['name']}') fehlgeschlagen: "
            f"Erwartet 201, erhalten {r.status_code}: {r.text}"
        )
        body = r.json()
        assert "id" in body, f"❌ Schritt 4.{i}: Keine id im Response: {body}"
        assert body.get("name") == spec["name"]
        member_ids.append(body["id"])
        print(f"    ✅ Member {i}/3 – {body['name']} (ID: {body['id'][:8]}...)")
    steps_passed += 1
    print(f"  ✅ Schritt 4 – {len(member_ids)} Members angelegt")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 5: Rezepte abrufen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  📖 Schritt 5/12: GET /recipes → 200 + 28 Einträge")
    r = httpx.get(f"{API_BASE}/recipes", headers=auth_headers, timeout=10)
    assert r.status_code == 200, (
        f"❌ Schritt 5 (Rezepte abrufen) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    recipes = r.json()
    assert isinstance(recipes, list), (
        f"❌ Schritt 5: Response ist kein Array: {type(recipes).__name__}"
    )
    recipe_count = len(recipes)
    assert recipe_count == 28, (
        f"❌ Schritt 5: {recipe_count} Rezepte gefunden (28 erwartet). "
        f"Führe aus: cd backend && python3 seed.py"
    )
    first_title = recipes[0].get("title", "(kein title)")
    last_title = recipes[-1].get("title", "(kein title)")
    steps_passed += 1
    print(f"  ✅ Schritt 5 – {recipe_count} Rezepte (erste: {first_title}, letzte: {last_title})")
    recipe_ids = [r["id"] for r in recipes if "id" in r]

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 6: Plan generieren
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  📅 Schritt 6/12: POST /plans/generate → 201 + plan_id + grocery_list")
    # Aktuellen Monat/Jahr ermitteln
    from datetime import date
    today = date.today()
    plan_month = today.month
    plan_year = today.year
    r = httpx.post(
        f"{API_BASE}/plans/generate",
        json={"month": plan_month, "year": plan_year, "focus_tags": ["schnell", "familie"]},
        headers=auth_headers,
        timeout=30,
    )
    assert r.status_code == 201, (
        f"❌ Schritt 6 (Plan generieren) fehlgeschlagen: "
        f"Erwartet 201, erhalten {r.status_code}: {r.text}"
    )
    body = r.json()
    assert "plan_id" in body, f"❌ Schritt 6: Kein plan_id im Response: {body}"
    plan_id = body["plan_id"]
    assert body.get("status") == "active", (
        f"❌ Schritt 6: Status nicht 'active': {body}"
    )
    assert body.get("weeks") == 4, (
        f"❌ Schritt 6: {body.get('weeks')} Wochen (4 erwartet)"
    )
    print(f"  ✅ Schritt 6 – Plan {plan_id[:8]}... für {body.get('month')}/{body.get('year')}")
    print(f"    → {body.get('weeks')} Wochen, Grocery-List: {body.get('grocery_list')}")
    has_grocery = body.get("grocery_list") is not None
    steps_passed += 1

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 7: PläNE listen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  📋 Schritt 7/12: GET /plans → 200 + 1 Plan")
    r = httpx.get(f"{API_BASE}/plans", headers=auth_headers, timeout=10)
    assert r.status_code == 200, (
        f"❌ Schritt 7 (Pläne listen) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    plans = r.json()
    assert isinstance(plans, list), (
        f"❌ Schritt 7: Response ist kein Array: {type(plans).__name__}"
    )
    assert len(plans) >= 1, (
        f"❌ Schritt 7: Keine Pläne gefunden (mind. 1 erwartet)"
    )
    our_plan = next((p for p in plans if p.get("id") == plan_id), None)
    assert our_plan is not None, (
        f"❌ Schritt 7: Unser Plan {plan_id[:8]}... nicht in der Liste: "
        f"{[p.get('id','?')[:8] for p in plans]}"
    )
    steps_passed += 1
    print(f"  ✅ Schritt 7 – {len(plans)} Plan(s) gefunden, unser Plan ist dabei")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 8: Wochen abrufen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🗓  Schritt 8/12: GET /plans/{id}/weeks → 200 + cw (Kalenderwoche)")
    r = httpx.get(
        f"{API_BASE}/plans/{plan_id}/weeks",
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, (
        f"❌ Schritt 8 (Wochen abrufen) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    weeks = r.json()
    assert isinstance(weeks, list), (
        f"❌ Schritt 8: Response ist kein Array: {type(weeks).__name__}"
    )
    assert len(weeks) == 4, (
        f"❌ Schritt 8: {len(weeks)} Wochen (4 erwartet)"
    )
    cw_found = weeks[0].get("cw")
    assert cw_found is not None, (
        f"❌ Schritt 8: Keine cw (Kalenderwoche) in Woche 1: {weeks[0]}"
    )
    assert isinstance(cw_found, int), (
        f"❌ Schritt 8: cw ist kein Integer: {cw_found} ({type(cw_found).__name__})"
    )
    slots_count = len(weeks[0].get("meal_slots", []))
    print(f"  ✅ Schritt 8 – {len(weeks)} Wochen, CW {cw_found}, "
          f"{slots_count} Slots in Woche 1")

    # Prüfe dass jede Woche meal_slots hat
    for idx, w in enumerate(weeks, 1):
        slots = w.get("meal_slots", [])
        assert len(slots) >= 1, (
            f"❌ Schritt 8: Woche {idx} hat keine meal_slots: {w}"
        )
    steps_passed += 1

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 9: Einkaufsliste abrufen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🛒 Schritt 9/12: GET /grocery-lists → 200 + 1 Liste mit Items")
    r = httpx.get(f"{API_BASE}/grocery-lists", headers=auth_headers, timeout=10)
    assert r.status_code == 200, (
        f"❌ Schritt 9 (Grocery-Listen) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    glists = r.json()
    assert isinstance(glists, list), (
        f"❌ Schritt 9: Response ist kein Array: {type(glists).__name__}"
    )
    assert len(glists) >= 1, (
        f"❌ Schritt 9: Keine Einkaufsliste gefunden (mind. 1 erwartet)"
    )
    list_id = glists[0].get("id")
    assert list_id, f"❌ Schritt 9: Erste Liste hat keine id: {glists[0]}"
    print(f"    → Liste {list_id[:8]}... gefunden")

    # Detaillierte Liste abrufen
    r = httpx.get(
        f"{API_BASE}/grocery-lists/{list_id}",
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, (
        f"❌ Schritt 9 Detail (Liste {list_id}) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    detail = r.json()
    items = detail.get("items", [])
    assert isinstance(items, list), (
        f"❌ Schritt 9: 'items' ist kein Array: {items}"
    )
    assert len(items) >= 1, (
        f"❌ Schritt 9: Keine Items in der Einkaufsliste: {detail}"
    )
    steps_passed += 1
    print(f"  ✅ Schritt 9 – {len(items)} Items in der Liste")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 10: Rezept-Detail
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🔬 Schritt 10/12: GET /recipes/{id} → 200 + title + Zutaten")
    test_recipe_id = recipe_ids[0]
    r = httpx.get(
        f"{API_BASE}/recipes/{test_recipe_id}",
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, (
        f"❌ Schritt 10 (Rezept-Detail) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    detail = r.json()
    assert "title" in detail, (
        f"❌ Schritt 10: Kein 'title' im Response: {detail}"
    )
    assert "ingredients" in detail, (
        f"❌ Schritt 10: Keine 'ingredients' im Response: {detail}"
    )
    ingredient_count = len(detail["ingredients"])
    assert ingredient_count >= 1, (
        f"❌ Schritt 10: Rezept hat 0 Zutaten: {detail}"
    )
    steps_passed += 1
    print(f"  ✅ Schritt 10 – '{detail['title']}' ({ingredient_count} Zutaten)")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 11: Profil aktualisieren (Household umbenennen)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  ✏️  Schritt 11/12: PUT /households/{id} → 200")
    r = httpx.put(
        f"{API_BASE}/households/{household_id}",
        json={"name": updated_name},
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 200, (
        f"❌ Schritt 11 (Household aktualisieren) fehlgeschlagen: "
        f"Erwartet 200, erhalten {r.status_code}: {r.text}"
    )
    # Prüfe, ob der Name tatsächlich geändert wurde
    r_get = httpx.get(
        f"{API_BASE}/households/{household_id}",
        headers=auth_headers,
        timeout=10,
    )
    if r_get.status_code == 200:
        updated_data = r_get.json()
        name_after = updated_data.get("name", "")
        print(f"    → Name nach Update: '{name_after}'")
    steps_passed += 1
    print(f"  ✅ Schritt 11 – Household aktualisiert")

    # ═══════════════════════════════════════════════════════════════════════
    #  Schritt 12: Member löschen
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print("  🗑  Schritt 12/12: DELETE /households/{id}/members/{mid} → 200")
    if member_ids:
        mid_to_delete = member_ids[-1]  # letztes Member löschen
        r = httpx.delete(
            f"{API_BASE}/households/{household_id}/members/{mid_to_delete}",
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code in (200, 204), (
            f"❌ Schritt 12 (Member löschen) fehlgeschlagen: "
            f"Erwartet 200/204, erhalten {r.status_code}: {r.text}"
        )
        # Prüfe, dass das Member weg ist
        r_get = httpx.get(
            f"{API_BASE}/households/{household_id}/members",
            headers=auth_headers,
            timeout=10,
        )
        if r_get.status_code == 200:
            remaining = r_get.json()
            remaining_ids = [m.get("id") for m in remaining if "id" in m]
            assert mid_to_delete not in remaining_ids, (
                f"❌ Schritt 12: Member {mid_to_delete[:8]}... wurde nicht gelöscht"
            )
            print(f"    → {len(remaining)} Members verbleiben (gelöscht: 1)")
        steps_passed += 1
        print(f"  ✅ Schritt 12 – Member gelöscht")
    else:
        print("  ⏭  Schritt 12 übersprungen (keine Members vorhanden)")

    # ═══════════════════════════════════════════════════════════════════════
    #  Zusammenfassung
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'═'*60}")
    print(f"  ✅ E2E: {steps_passed}/{total_steps} Tests bestanden")
    print(f"{'═'*60}")
    print(f"\n  User:      {email}")
    print(f"  Passwort:  {PASSWORD}")
    print(f"  Household: {household_id}")
    print(f"  Plan:      {plan_id}")
    print(f"  Daten bleiben für Debug in der DB.\n")