# Sprossa – Familien-Ernährungsplaner

**Status:** Early Development (v0.2.0)
**Finaler Name:** SPROSSA 🌱 – siehe docs/naming.md

## Übersicht

Sprossa ist ein SaaS-Dienst, der automatisiert **monatliche Ernährungspläne** für Familien erstellt – inkl. Rezepten und intelligenter Einkaufsliste. Kernstrategie: **Cook Once, Eat Twice** – einmal kochen, zweimal essen. Reduziert Koch-Aufwand um bis zu 40 %.

## Architektur

```
monatsmenue/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI-App + Router-Wiring
│   │   ├── core/
│   │   │   ├── auth.py           # Pure-Python JWT + Passwort-Hashing
│   │   │   ├── config.py         # Settings via Pydantic (.env)
│   │   │   ├── database.py       # Async-Session (SQLAlchemy)
│   │   │   └── dependencies.py   # FastAPI-Dependencies (get_current_user_id)
│   │   ├── models/
│   │   │   └── database.py       # SQLAlchemy-ORM (11 Tabellen)
│   │   ├── schemas/
│   │   │   └── api.py            # Pydantic-Request/Response-Schemas
│   │   ├── services/
│   │   │   ├── plan_generator.py # Plan-Generator (Monats-Wochenplan-Logik)
│   │   │   └── grocery_engine.py # Einkaufslisten-Engine
│   │   └── routes/
│   │       ├── auth.py           # POST /register, /login, GET /me
│   │       ├── households.py     # CRUD Household + Member
│   │       └── family.py         # CRUD Recipes/Ingredients + Plan/Grocery-Generierung + Stripe
│   ├── tests/
│   │   ├── run_tests.py          # Sprint 1: 15 Tests (Plan + Grocery Core)
│   │   └── test_api_sprint2.py   # Sprint 2: 21 Tests (Auth + CRUD + Stripe)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                     # Next.js 15 + Tailwind CSS 4
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Landingpage
│   │   ├── login/page.tsx
│   │   └── features/page.tsx
│   ├── package.json
│   ├── tailwind.config.ts
│   └── ...
├── docs/
│   ├── datenmodell.md
│   └── naming.md
├── docker-compose.yml
└── README.md
```

## Tech-Stack

| Komponente | Technologie |
|------------|-------------|
| Frontend   | React/Next.js 15 + Tailwind CSS 4 |
| Backend    | FastAPI (Python 3.13+) |
| DB         | PostgreSQL 16 (SQLAlchemy async) |
| Auth       | JWT (HMAC-SHA256 Selbstbau, ab lösbar durch python-jose) |
| Payments   | Stripe (Scaffold: Checkout-Session-Stub + Webhook-Stub) |

## Schnellstart

```bash
# 1. PostgreSQL
docker compose up -d db

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install && npm run dev

# 4. Tests
cd backend && python3 tests/run_tests.py && python3 tests/test_api_sprint2.py
```

## API-Endpunkte (Sprint 2 Stand)

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | /health | Healthcheck |
| POST | /api/v1/auth/register | Registrierung (Email+Passwort) → Token |
| POST | /api/v1/auth/login | Login → Token |
| GET | /api/v1/auth/me | Eigenes Profil (geschützt) |
| POST | /api/v1/households | Household anlegen |
| GET | /api/v1/households/{id} | Household abrufen |
| POST | /api/v1/households/{id}/members | Familienmitglied hinzufügen |
| GET | /api/v1/households/{id}/members | Mitglieder auflisten |
| DELETE | /api/v1/households/{id}/members/{mid} | Mitglied löschen |
| POST | /api/v1/ingredients | Zutat anlegen |
| GET | /api/v1/ingredients | Zutaten auflisten |
| POST | /api/v1/recipes | Rezept anlegen |
| GET | /api/v1/recipes | Rezepte auflisten |
| GET | /api/v1/recipes/{id} | Rezept abrufen |
| POST | /api/v1/plans/generate | Monatsplan generieren |
| POST | /api/v1/grocery/generate | Einkaufsliste generieren |
| POST | /api/v1/stripe/create-checkout-session | Stripe-Checkout (Stub) |
| POST | /api/v1/stripe/webhook | Stripe-Webhook (Stub) |

## Datenmodell (Kern)

Siehe [docs/datenmodell.md](docs/datenmodell.md) für das vollständige Modell.

**Domain-Regeln (alle durch Tests abgedeckt):**
1. MonthlyPlan hat 4 oder 5 WeeklyPlans
2. 7 Dinner-Slots pro Woche
3. CookOnce-EatTwice: max 2 Rezepte/Woche doppelt belegt
4. Keine Rezept-Wiederholung innerhalb 7 Tagen
5. Keine Allergene bei entsprechenden Membern
6. Einkaufsliste summiert Zutaten (exkl. CookOnce-Repeats)
7. Passwort-Hashing mit Salt
8. JWT-Tokens mit Ablauf + Signatur-Prüfung

## TDD-Status

**36/36 Tests – ALLE GREEN** ✅

**Sprint 1 – Core-Logik (15 Tests):**
- weeks_in_month (4 vs 5 Wochen pro Monat)
- WeeklyPlan-Skeleton (7 Slots, CookOnce, keine Duplikate)
- MonthlyPlan (Wochenanzahl, Nummerierung)
- GroceryList (Summierung, CookOnce-Ignorierung, Gruppierung, Multiplikator)

**Sprint 2 – Auth + API + Stripe (21 Tests):**
- AuthCore: Passwort-Hashing (Salt, PBKDF2), JWT (Erzeugung, Decodierung, Ablauf, Signatur)
- AuthFlows: Registrierung, Login, Token-Validierung
- CRUD: Household, Member, Recipe, Ingredient
- Integration: Rezepte → Monatsplan → Einkaufsliste (E2E)
- Stripe: Checkout-Stub, Webhook-Stub, Preis-szenarien

## Lizenz

Proprietär – Sprossa