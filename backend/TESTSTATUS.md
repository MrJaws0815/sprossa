# Teststatus Backend — Task N9

**Datum:** 06.11.2026 · **Scope:** `backend/tests/` (kein Produktcode geändert)

## 1. Ergebnis

| Stand | Kommando | Ergebnis |
|---|---|---|
| vorher (Sitzungsbeginn) | `pytest tests/ -q` | **201 passed**, 0 failed, 9 warnings |
| vorher (E2E separat) | `pytest tests/test_e2e_flow.py -q` | **1 passed** |
| nachher | `pytest tests/ -q` | **235 passed**, 0 failed, 9 warnings, 35.39s |
| nachher (E2E separat) | `pytest tests/test_e2e_flow.py -q` | **1 passed**, 1.29s |

Differenz +34 Tests = **+28 neue Exception-Case-Tests** (dieses Task) + **+6**
`test_grocery_generate_body.py` (parallel von einem anderen Worker angelegt,
nicht Teil dieses Tasks).

**Kernbefund:** Die in N9 genannten „2 Test-Fixture-Fails" existierten zum
Sitzungsbeginn **nicht mehr** — beide Ursachen waren bereits im Working Tree
behoben (E2E-Assertion dynamisch, async Fixtures über `asyncio_mode = auto`).
Nachgestellt und gehärtet statt neu „gefixt".

## 2. Die beiden N9-Fehler — Ursache und Stand

### 2.1 `test_e2e_flow.py`: 28-Rezepte-Assertion (Task 27)

- **Symptom:** `AssertionError: 314 Rezepte gefunden (28 erwartet)`.
- **Ursache:** hartkodierte Kataloggröße im Test. Der Katalog ist seit dem
  Import auf 320 Zeilen gewachsen (davon 6 Fixture-Reste, siehe 4.1); das
  Produkt war korrekt, die Erwartung veraltet.
- **Stand:** Fix war vorhanden, aber zu schwach — die Assertion war auf
  `recipe_count > 0` abgesenkt. Ein Katalog mit einem einzigen Rezept hätte den
  Test bestanden (False Green).
- **Fix:** `recipe_count >= 28` (Untergrenze = geseedetes System) mit klarer
  Fehlermeldung; Docstring auf „>= 28 Seed-Rezepte" korrigiert. Bewusst keine
  echte DB-Count-Abfrage: der Test läuft gegen die Live-API und darf keine
  DB-Credentials brauchen.

### 2.2 `test_plan_generator_db.py`: `'async_generator' object is not subscriptable` (Task 28)

- **Symptom:** Fixture `demo_household` liefert einen async generator statt des
  Dicts; `demo_household["household"]` schlägt fehl.
- **Ursache:** async Fixtures ohne `@pytest_asyncio.fixture`. Trat nur in
  striktem asyncio-Modus auf.
- **Stand:** behoben über `asyncio_mode = auto` in `pytest.ini` (gültige,
  dokumentierte Lösung — kein Decorator nötig). Nachgeprüft: Modul läuft
  isoliert mit 19 passed; Fixture-Cleanup greift (siehe 4.1).
- **Kein Code-Fix nötig.** Würde `asyncio_mode` je auf `strict` gestellt,
  müssen alle async Fixtures in `conftest.py`/Modulen `pytest_asyncio.fixture`
  bekommen — im Bericht vermerkt, nicht vorsorglich umgebaut (unnötiger Churn).

## 3. Task 35 / H4 — Exception Cases auf 100 %

Neu: `backend/tests/test_exception_cases.py` (28 Tests). Die Matrix aus
Launch-Kriterium H4 ist damit vollständig abgedeckt:

| Matrix-Fall | Tests | Geprüftes Verhalten |
|---|---|---|
| Allergien | 4 | 400 bei 0 Treffern; Umlaut/ASCII-Normalisierung (`nüsse` = `nuesse`); Allergie als String statt Liste; gemischter Katalog → Allergen fliegt raus, Rest bleibt planbar |
| Abneigungen | 2 | weiche Regel: kleiner Katalog → Plan entsteht trotzdem; `"Karotten, Pilze"` als String wird geparst |
| Kinderalter | 9 (parametrisiert) | Grenzwerte 0/3/4/7/8/12/13, `age=None`, 99; `portion_factor` aus Profil schlägt Alter; negativer Faktor wird ignoriert |
| Haushaltsgröße 1–8 | 4 | 1 Person → 1.0 Portionen, Multiplier 0.25; 8 Personen → 5.4 Portionen, Multiplier 1.35; leere Mitgliederliste → 0.0 ohne Division-durch-Null |
| fehlende Zutaten | 2 | Rezepte ohne Zutaten → Plan + leere Einkaufsliste, kein Crash; gemischt → Items > 0 |
| Ernährungsprofil | 1 | vegan ohne Treffer → 400 „Ernährungsprofil" |
| Fokus-Tags / Saison | 2 | 400 mit klarer Meldung statt stillem Fallback |
| Platzhalter-Katalog | 1 | nur „Testrezept …" → 400, keine Platzhalter im Plan |

Alle 28 Tests grün. Sie beschreiben Soll-Verhalten, das im Produktcode bereits
korrekt implementiert ist (`plan_generator.py` Z. 960–1035). Kein Test wurde
abgeschwächt, um grün zu werden; kein `xfail`/`skip` gesetzt.

**Testhygiene:** Jeder DB-Test legt ausschließlich eigene Zeilen an und löscht
sie kind-first über die eigene `household_id` (Grocery-Items → Lists → Slots →
Weekly → Monthly → RecipeIngredients → Recipes → Members → Household → User).
Verifiziert nach dem Lauf: `users_exc=0`, `haushalte_fixture=0`.

## 4. Bewusst NICHT gefixt

### 4.1 Reste eines abgebrochenen Testlaufs in der Test-DB

In `sprossa_test` liegen **6 Rezepte „Fixturegericht 1–6"** (Haushalt
`e0d039c0…`, „Test-Plan-Haushalt", `created_at 06:31 UTC`), dazu **3 leere
Haushalte gleichen Namens vom 24.10.2026** (`cd188311…`, `ef293f11…`,
`64004b97…`, jeweils 0 Rezepte). Der Haushalt von heute stammt aus einem
**abgebrochenen** pytest-Lauf (parallel laufender Worker), nicht aus dem
Fixture-Cleanup: ein isolierter Lauf von `test_plan_generator_db.py` lässt
nachweislich null Zeilen zurück (Rezeptzahl 320 vor und nach dem Lauf
unverändert, Haushaltszahl unverändert).

**Nicht gelöscht**, weil (a) die Vorgabe lautet, keine Testdaten ohne Prüfung zu
entfernen, und (b) ein Fremdlauf sie theoretisch noch referenzieren könnte.
Empfehlung: nach Abstimmung mit dem parallel arbeitenden Worker einmalig per
SQL entfernen — Kriterium `household.name = 'Test-Plan-Haushalt'` (kind-first).

### 4.2 Platzhalter-Filter kennt Test-Fixture-Titel nicht (Produktcode)

`_is_placeholder_title()` filtert „Testrezept…", „Rezept A/B/C", „Einziges
Rezept" — **nicht** „Fixturegericht"/„Probegericht". Solange Test-Fixtures
Rezepte im globalen Katalog anlegen, können sie bei abgebrochenen Läufen in
Nutzerplänen landen (H1-Kriterium). Ursache ist die fehlende Scoping-Logik
(globaler Katalog ohne `is_curated`-Flag), nicht der Test.

**Nicht gefixt:** erfordert `app/` (verboten, dort arbeitet parallel jemand).
Naheliegende, aber falsche Test-Lösung wäre, Fixtures „Testrezept …" zu nennen —
dann filtert der Generator die Fixtures selbst weg und die Tests würden mit 400
scheitern. Empfehlung an Produkt: `is_curated`-Flag oder Haushalts-Scoping.

### 4.3 `tests/test_onboarding.py` sammelt 0 Tests

Die Datei ist ein **manuelles Skript** (`main()` + `sys.exit`), keine
pytest-Suite; sie taucht in `pytest --collect-only` mit 0 Tests auf und täuscht
Deckung vor. Inhaltlich ist sie ein Duplikat von `test_e2e_flow.py` (12 Schritte,
grün).

**Nicht umgebaut:** Sie nutzt hartkodiert `month=10, year=2026`. `MonthlyPlanCreate`
erlaubt aber nur aktuellen und Folgemonat (`app/schemas/api.py` Z. 196–203) —
Oktober 2026 wird im November 2026 abgelehnt. Eine 1:1-Umwandlung würde einen
roten Test erzeugen, der nichts über das Produkt aussagt. Empfehlung: Datei nach
`scripts/` verschieben oder löschen, wenn `test_e2e_flow.py` als einziger
E2E-Träger bestätigt ist.

### 4.4 API-Response-Inkonsistenz (`plan_id` vs. `id`, Task 29/56)

Im E2E-Test sichtbar, aber Produktcode-Thema (Schemas + Frontend-Consumer).
Nicht angefasst, da `app/` gesperrt ist und eine Test-Anpassung den Bruch
lediglich verstecken würde.

## 5. Geänderte Dateien

| Datei | Änderung |
|---|---|
| `backend/tests/test_exception_cases.py` | **neu**, 28 Exception-Case-Tests (Task 35 / H4) |
| `backend/tests/test_e2e_flow.py` | Assertion `> 0` → `>= 28`, Docstring präzisiert |

Keine Änderung an `app/`, an Seed-Daten, `dist/` oder `social/`.
