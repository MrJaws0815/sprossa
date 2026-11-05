"""Plan-Generator: Kernlogik für automatische Wochen-/Monatspläne

Domain-Regeln (TDD-Anker):
1. Ein MonthlyPlan hat 4-5 WeeklyPlans je nach Monat
2. Mindestens 5 Hauptmahlzeiten pro Woche (Slots mit meal_type=dinner)
3. CookOnce-EatTwice: max 2 Rezepte pro Woche, die doppelt belegt werden
4. Keine Wiederholung desselben Rezepts innerhalb 7 Tagen
5. Berücksichtigt Member-Allergien (kein Rezept mit Allergen)
6. Berücksichtigt Haushalts-Präferenzen (vegetarisch, etc.)

Sprint D – Erweiterungen:
- Task 16: Ess-Typ-Filter (dietary_profile vom Household)
- Task 17: Allergen-Prüfung (Member-Allergien gegen Zutaten)
- Task 19: Abwechslungs-Rad (letzte 4 Wochen ausschließen)
- Task 20: Balanceregel (max 2x Nudeln/Reis/Kartoffeln/Suppe pro Woche)
- Task 21: Portions-Faktor (Altersgewichte)
"""
import random
import re
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    GroceryItem, GroceryList, Ingredient, MealSlot, MonthlyPlan, Recipe,
    RecipeIngredient, WeeklyPlan,
)
from app.repositories.plan import MonthlyPlanRepository, WeeklyPlanRepository, MealSlotRepository
from app.repositories.recipe import RecipeRepository


# ─── Allergen-Mapping-Tabelle (Task 17) ────────────────────────────────────

ALLERGEN_MAP: dict[str, list[str]] = {
    "gluten": ["Weizenmehl", "Mehl", "Nudeln", "Brot", "Haferflocken", "Dinkel", "Grieß"],
    "laktose": ["Milch", "Sahne", "Joghurt", "Butter", "Käse", "Frischkäse", "Quark", "Kefir"],
    "nuesse": [
        "Mandeln", "Walnüsse", "Haselnüsse", "Cashewkerne", "Erdnüsse", "Pistazien",
        "Pinienkerne", "Pecannüsse", "Paranüsse", "Macadamia", "Marzipan",
        "Nuss", "Erdnuss", "Haselnuss", "Walnuss", "Muskatnuss", "Kokosnuss",
    ],
    "ei": ["Ei", "Eier", "Eigelb", "Eiweiß", "Eiern"],
    "soja": ["Soja", "Sojasauce", "Tofu", "Sojamilch", "Sojajoghurt", "Edamame"],
    "fisch": ["Fisch", "Lachs", "Thunfisch", "Forelle", "Sardine", "Makrele"],
    "schalenfrüchte": ["Garnelen", "Krabben", "Muscheln", "Hummer"],
}

# Kategorie-Mapping für Balanceregel (Task 20) – via recipe.title
RECIPE_CATEGORY_RULES: dict[str, list[str]] = {
    "Nudeln": ["Spaghetti", "Nudel", "Pasta", "Tagliatelle", "Fettuccine", "Rigatoni"],
    "Reis": ["Reis", "Risotto", "Paella"],
    "Kartoffeln": ["Kartoffel", "Bratkartoffel", "Pommes", "Stampf", "Gratin"],
    "Suppe": ["Suppe", "Eintopf", "Cremesuppe", "Klare Suppe"],
}

MAX_PER_CATEGORY: dict[str, int] = {
    "Nudeln": 2,
    "Reis": 2,
    "Kartoffeln": 2,
    "Suppe": 2,
}

# ─── Platzhalter-/Demo-Rezepte (Datenbereinigung) ─────────────────────────
# Rezepte aus dem Demo-/Test-Setup („Testrezept 1–6“, „Rezept A/B/C“,
# „Einziges Rezept“) liegen im globalen Katalog und würden in Pläne echter
# Nutzer einfließen. Sie werden bei der Generierung ausgeschlossen.
PLACEHOLDER_TITLE_PATTERNS: tuple[str, ...] = (
    "testrezept",
    "rezept a",
    "rezept b",
    "rezept c",
    "einziges rezept",
)


def _is_placeholder_title(title: str | None) -> bool:
    """True, wenn der Rezepttitel ein Demo-/Test-Platzhalter ist.

    Prüfung case-insensitive:
      - Titel beginnt mit „Testrezept“
      - Titel ist genau „Rezept A/B/C“ (auch mit Klammerzusatz, z. B.
        „Rezept A (Test)“)
      - Titel enthält „Einziges Rezept“
    """
    normalized = (title or "").lower().strip()
    if not normalized:
        return False
    if normalized.startswith("testrezept"):
        return True
    if "einziges rezept" in normalized:
        return True
    # Exakte Platzhalter-Titel „Rezept A/B/C“ (optional mit Zusatz in Klammern)
    for letter in ("a", "b", "c"):
        prefix = f"rezept {letter}"
        if normalized == prefix or normalized.startswith((prefix + " (", prefix + "(")):
            return True
    return False


# ─── Markertyp für Plan-Konfiguration ────────────────────────────────────

class GeneratorConfig:
    """Konfiguration für einen Generierungs-Durchlauf."""
    def __init__(
        self,
        household_id: UUID,
        month: int,
        year: int,
        member_ids: list[UUID],
        recipe_ids: list[UUID],
        cook_once_eat_twice_count: int = 2,
        cook_once_enabled: bool = True,          # Task 83: CookOnce steuerbar
        cook_once_count: Optional[int] = None,   # Task 83: N Rezepte/Woche erzwingen
        meals_per_week: int = 5,       # Anzahl Hauptgerichte (dinner)
        include_breakfast: bool = False,
        focus_tags: Optional[list[str]] = None,
        # Sprint D – Erweiterungen
        dietary_profile: Optional[dict] = None,      # Task 16
        members: Optional[list[dict]] = None,         # Task 17 + 21 (allergies, age)
        total_portions: float = 0.0,                  # Task 21
    ):
        self.household_id = household_id
        self.month = month
        self.year = year
        self.member_ids = member_ids
        self.recipe_ids = recipe_ids
        self.cook_once_eat_twice_count = cook_once_eat_twice_count
        # Task 83: cook_once_count ist die neue, explizite Anzahl. Aus
        # Kompatibilitätsgründen fällt sie auf den alten Parameter zurück.
        self.cook_once_enabled = cook_once_enabled
        self.cook_once_count = (
            cook_once_count if cook_once_count is not None else cook_once_eat_twice_count
        )
        self.meals_per_week = meals_per_week
        self.include_breakfast = include_breakfast
        self.focus_tags = focus_tags or []
        self.dietary_profile = dietary_profile or {}
        self.members = members or []
        self.total_portions = total_portions


def weeks_in_month(month: int, year: int) -> int:
    """Gibt die Anzahl der Planungswochen für einen Monat zurück (4 oder 5).

    Domain-Regel: 28 Tage → 4 Wochen, 29+ Tage → 5 Wochen.
    """
    import calendar
    days = calendar.monthrange(year, month)[1]
    return 4 if days <= 28 else 5


# ─── Task 85 – Einkaufs-Segmentierung nach Einkaufstagen ───────────────────

_WEEKDAY_LABEL: dict[int, str] = {
    1: "Mo", 2: "Di", 3: "Mi", 4: "Do", 5: "Fr", 6: "Sa", 7: "So",
}


def _segment_slots_by_shopping_days(
    slots: list,
    shopping_days: Optional[list],
) -> list[tuple[Optional[str], list]]:
    """Teilt die Slots einer Woche anhand der Einkaufstage in Segmente.

    Jeder Einkaufstag beginnt ein neues Segment; das Segment deckt Slots bis
    zum Vortag des nächsten Einkaufstags. Beispiel [1, 4] → Mo–Mi und Do–So.

    Ohne (gültige) shopping_days wird genau ein Segment zurückgegeben, damit
    das bisherige Verhalten (eine Liste pro Woche) unverändert bleibt.
    """
    all_slots = list(slots)
    if not shopping_days:
        return [(None, all_slots)]

    days: list[int] = []
    for raw in shopping_days:
        try:
            day = int(raw)
        except (TypeError, ValueError):
            continue
        if 1 <= day <= 7 and day not in days:
            days.append(day)
    days.sort()
    if not days:
        return [(None, all_slots)]

    segments: list[tuple[Optional[str], list]] = []
    start = 1
    for boundary in days:
        end = boundary - 1
        if end >= start:
            label = f"Einkauf {_WEEKDAY_LABEL[start]} bis {_WEEKDAY_LABEL[end]}"
            segments.append((label, [s for s in all_slots if start <= s.day_of_week <= end]))
        start = boundary
    if start <= 7:
        label = f"Einkauf {_WEEKDAY_LABEL[start]} bis {_WEEKDAY_LABEL[7]}"
        segments.append((label, [s for s in all_slots if start <= s.day_of_week <= 7]))

    return segments or [(None, all_slots)]


# ─── Task 16 – Ess-Typ-Filter ──────────────────────────────────────────────

def _categorize_recipe_by_title(title: str) -> Optional[str]:
    """Bestimmt die Kategorie eines Rezepts anhand des Titels (Task 20)."""
    title_lower = title.lower()
    for category, keywords in RECIPE_CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in title_lower:
                return category
    return None


def _collect_diet_profiles(dietary_profile: dict) -> list[str]:
    """Sammelt alle Ernährungsweisen aus einem (evtl. verschachtelten) Profil.

    Unterstützt:
      - "diet_types": ["vegetarisch", ...]  (Frontend-Format)
      - "type": "vegetarisch"               (altes Format)
      - "preferences": "vegan" | ["vegan"]  (weiteres Format)
    Unbekannte Keys werden ignoriert, nie gecrasht.
    """
    profile = dietary_profile or {}
    if not isinstance(profile, dict):
        return []

    raw: list = []
    diet_types = profile.get("diet_types")
    if isinstance(diet_types, str):
        raw.append(diet_types)
    elif isinstance(diet_types, (list, tuple)):
        raw.extend(diet_types)

    single = profile.get("type")
    if isinstance(single, str):
        raw.append(single)

    prefs = profile.get("preferences")
    if isinstance(prefs, str):
        raw.append(prefs)
    elif isinstance(prefs, (list, tuple)):
        raw.extend(prefs)

    return [str(p).lower().strip() for p in raw if p]


def _filter_by_diet(recipes: list[Recipe], dietary_profile: dict) -> list[Recipe]:
    """Task 16: Filtere Rezepte basierend auf der Ernährungsweise des Haushalts.

    dietary_profile kann "diet_types" (Liste), "type" (String) oder
    "preferences" enthalten. Strengstes Profil gewinnt:
    vegan > vegetarisch/veggie > vollkost.
    Tags in recipes: fleisch, fisch, vegetarisch, vegan, veggie
    """
    profiles = set(_collect_diet_profiles(dietary_profile))
    if "vegan" in profiles:
        profile = "vegan"
    elif profiles & {"vegetarisch", "veggie"}:
        profile = "vegetarisch"
    else:
        profile = "vollkost"

    if profile == "vollkost":
        return recipes

    filtered: list[Recipe] = []
    for r in recipes:
        tags = [t.lower().strip() for t in (r.tags or [])]
        if profile == "vegan":
            # Vegan: kein Fleisch, kein Fisch, keine Milch, keine Eier
            if "fleisch" in tags or "fisch" in tags or "milch" in tags or "eier" in tags:
                continue
        elif profile == "vegetarisch":
            # Vegetarisch: kein Fleisch, kein Fisch
            if "fleisch" in tags or "fisch" in tags:
                continue
        filtered.append(r)
    return filtered


# ─── Saison-Filter ─────────────────────────────────────────────────────────

SEASON_BY_MONTH: dict[int, str] = {
    3: "frühling", 4: "frühling", 5: "frühling",
    6: "sommer", 7: "sommer", 8: "sommer",
    9: "herbst", 10: "herbst", 11: "herbst",
    12: "winter", 1: "winter", 2: "winter",
}

SEASON_TAGS: set[str] = {
    "frühling", "fruehling", "sommer", "herbst", "winter", "saisonal",
}


def _season_for_month(month: int) -> str:
    return SEASON_BY_MONTH[month]


def _filter_by_season(recipes: list[Recipe], month: int) -> list[Recipe]:
    """Filtert Rezepte nach Saison-Tags passend zum Zielmonat.

    - Rezept ohne Saison-Tag: immer erlaubt.
    - Rezept nur mit Tag "saisonal": immer erlaubt.
    - Rezept mit Saison-Tag(en): nur erlaubt, wenn der Zielmonat dabei ist.
    """
    target = _season_for_month(month)
    allowed: list[Recipe] = []
    for r in recipes:
        tags = {t.lower().strip() for t in (r.tags or [])}
        season_tags = tags & SEASON_TAGS
        if not season_tags:
            allowed.append(r)
            continue
        explicit = season_tags - {"saisonal"}
        if not explicit:
            # Nur "saisonal" -> ganzjährig erlaubt
            allowed.append(r)
            continue
        if target in explicit:
            allowed.append(r)
    return allowed


# ─── Task 17 – Allergen-Prüfung ────────────────────────────────────────────

def _build_ingredient_index(
    recipes: list[Recipe],
) -> tuple[dict[UUID, str], dict[UUID, list[UUID]], dict[UUID, str]]:
    """Baut Indizes über recipe → ingredients und ingredient → name.

    Returns:
        (ingredient_id -> name, recipe_id -> [ingredient_ids], ingredient_id -> category)
    """
    ing_id_to_name: dict[UUID, str] = {}
    ing_id_to_cat: dict[UUID, str] = {}
    recipe_ing_ids: dict[UUID, list[UUID]] = {}

    for r in recipes:
        r_ing_ids: list[UUID] = []
        for ri in (r.ingredients or []):
            ing_id = ri.ingredient_id
            r_ing_ids.append(ing_id)
            if ing_id not in ing_id_to_name and ri.ingredient:
                ing_id_to_name[ing_id] = ri.ingredient.name
                ing_id_to_cat[ing_id] = ri.ingredient.category
        recipe_ing_ids[r.id] = r_ing_ids

    return ing_id_to_name, recipe_ing_ids, ing_id_to_cat


def _norm_allergen(value: str) -> str:
    """Normalisiert Allergen-/Zutatenbegriffe für den Vergleich.

    Umlaute werden aufgelöst, damit „nüsse" (Nutzereingabe) und „nuesse"
    (Tag-Schreibweise im Katalog) zusammenfinden. Ohne diese Normalisierung
    lief der Filter ins Leere: „nüsse" war kein Schlüssel in ALLERGEN_MAP,
    also wurde gar nicht gefiltert.
    """
    table = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    text = (value or "").lower().strip().translate(table)
    # Doppelbuchstaben zusammenziehen: „nuesse" -> „nuse", „erdnuss" -> „erdnus".
    # Sonst trifft die Schreibweise mit Umlaut („nüsse") nie den Stamm („nuss").
    return re.sub(r"(.)\1+", r"\1", text)


# Synonyme, die Nutzer tippen, aber nicht Schlüssel der Tabelle sind.
ALLERGEN_ALIASES: dict[str, str] = {
    "nuss": "nuesse",
    "nuesse": "nuesse",
    "nuts": "nuesse",
    "schalenfruechte": "nuesse",
    "milch": "laktose",
    "dairy": "laktose",
    "eier": "ei",
    "egg": "ei",
}


def _ingredient_matches(ing_norm: str, keywords: set[str]) -> bool:
    """True, wenn eine Zutat zu einem Allergen-Keyword passt.

    Kurze Keywords („ei") nur als ganzes Wort, längere auch als Teilstring
    („mandeln" trifft „mandeln (gemahlen)").
    """
    if not ing_norm:
        return False
    if ing_norm in keywords:
        return True
    tokens = set(re.split(r"[^a-z0-9]+", ing_norm))
    for kw in keywords:
        if not kw:
            continue
        if len(kw) <= 3:
            if kw in tokens:
                return True
        elif kw in ing_norm:
            return True
    # Zusammengesetzte Zutaten: „Erdnussöl" beginnt mit dem Stamm „erdnus",
    # „Haselnussmus" mit „haselnus" — Präfix-Treffer, kein „genus"-Fehlalarm.
    for tok in tokens:
        for kw in keywords:
            if len(kw) >= 4 and tok.startswith(kw):
                return True
    return False


def _allergen_index() -> tuple[dict[str, list[str]], dict[str, str]]:
    """Normalisierte Fassung von ALLERGEN_MAP und ALLERGEN_ALIASES.

    Beide Tabellen sind in Klarschrift gepflegt; der Vergleich läuft über die
    normalisierten Schlüssel („Nüsse" -> „nues").
    """
    index = {_norm_allergen(k): v for k, v in ALLERGEN_MAP.items()}
    aliases = {_norm_allergen(k): _norm_allergen(v) for k, v in ALLERGEN_ALIASES.items()}
    return index, aliases


def _resolve_allergen(allergy: str) -> str:
    index, aliases = _allergen_index()
    key = _norm_allergen(allergy)
    return aliases.get(key, key)


def _build_allergen_set(member_allergies: list[str]) -> set[str]:
    """Baut ein Set von Allergen-Keywords (normalisiert), die Zutaten triggern."""
    if not member_allergies:
        return set()
    index, _ = _allergen_index()
    allergen_set: set[str] = set()
    for allergy in member_allergies:
        for name in index.get(_resolve_allergen(allergy), []):
            allergen_set.add(_norm_allergen(name))
    return allergen_set


def _build_allergen_tags(member_allergies: list[str]) -> set[str]:
    """Baut das Set der Rezept-Tags, die als Allergen gelten (z. B. „nuesse")."""
    if not member_allergies:
        return set()
    index, _ = _allergen_index()
    tags: set[str] = set()
    for allergy in member_allergies:
        key = _resolve_allergen(allergy)
        if key in index:
            tags.add(key)
    return tags


def _build_allergen_categories(member_allergies: list[str]) -> set[str]:
    """Baut ein Set von ingredient.category-Werten (normalisiert), die Allergene triggern."""
    category_map: dict[str, set[str]] = {
        "laktose": {"milchprodukte & eier", "dairy"},
        "fisch": {"fisch", "fish"},
    }
    cats: set[str] = set()
    for allergy in member_allergies:
        key = _resolve_allergen(allergy)
        if key in category_map:
            cats.update(category_map[key])
    return cats


def _filter_by_allergens(
    recipes: list[Recipe],
    member_allergies: list[str],
    ing_id_to_name: dict[UUID, str],
    ing_id_to_cat: dict[UUID, str],
    recipe_ing_ids: dict[UUID, list[UUID]],
) -> list[Recipe]:
    """Task 17: Entferne Rezepte, deren Zutaten Allergene enthalten."""
    if not member_allergies:
        return recipes

    allergen_names = _build_allergen_set(member_allergies)
    allergen_tags = _build_allergen_tags(member_allergies)
    allergen_cats = _build_allergen_categories(member_allergies)

    filtered: list[Recipe] = []
    for r in recipes:
        # 1. Tag-Ebene: der Katalog taggt Allergene bereits (gluten, nuesse, ...).
        recipe_tags = {_norm_allergen(t) for t in (r.tags or [])}
        if recipe_tags & allergen_tags:
            continue

        # 2. Zutaten-Ebene: fängt Rezepte, die (noch) nicht getaggt sind.
        has_allergen = False
        for ing_id in recipe_ing_ids.get(r.id, []):
            ing_name = _norm_allergen(ing_id_to_name.get(ing_id, ""))
            ing_cat = _norm_allergen(ing_id_to_cat.get(ing_id, ""))
            if _ingredient_matches(ing_name, allergen_names):
                has_allergen = True
                break
            if ing_cat in allergen_cats:
                has_allergen = True
                break
        if not has_allergen:
            filtered.append(r)
    return filtered


def _parse_dislikes(dietary_profile: dict) -> set[str]:
    """Liest Abneigungen aus dem Profil und normalisiert sie.

    Frontend liefert `disliked_ingredients` als kommaseparierten String
    (z.B. "Pilze, Rosenkohl"). Listen und Strings werden beide akzeptiert.
    Rückgabe: Set aus kleingeschriebenen, getrimmten Begriffen.
    """
    profile = dietary_profile or {}
    if not isinstance(profile, dict):
        return set()
    raw = profile.get("disliked_ingredients")
    if raw is None:
        raw = profile.get("dislikes")
    if isinstance(raw, str):
        parts = raw.replace("\n", ",").split(",")
    elif isinstance(raw, (list, tuple)):
        parts = list(raw)
    else:
        return set()
    return {str(p).strip().lower() for p in parts if str(p).strip()}


def _filter_by_dislikes(
    recipes: list[Recipe],
    disliked: set[str],
    ing_id_to_name: dict[UUID, str],
    recipe_ing_ids: dict[UUID, list[UUID]],
    min_pool: int = 20,
) -> list[Recipe]:
    """Abneigungen = WEICHE Regel: bevorzugt meiden, aber nicht blockieren.

    - Rezepte ohne Abneigung bleiben immer im Pool.
    - Rezepte mit Abneigung werden nur dann ausgeschlossen, wenn danach
      noch genug Auswahl übrig bleibt (>= min_pool). Sonst bleiben sie
      als Fallback drin — der Plan darf nicht an Geschmack scheitern.
    """
    if not disliked:
        return recipes

    # Keywords defensiv normalisieren: Aufrufer soll _parse_dislikes nutzen,
    # aber ein roher String/Set (z.B. {"PILZE"}) darf den Filter nicht aushebeln.
    disliked = {str(k).strip().lower() for k in disliked if str(k).strip()}
    if not disliked:
        return recipes

    clean: list[Recipe] = []
    disliked_hits: list[Recipe] = []
    for r in recipes:
        hit = False
        for ing_id in recipe_ing_ids.get(r.id, []):
            ing_name = (ing_id_to_name.get(ing_id, "") or "").strip().lower()
            if not ing_name:
                continue
            if _ingredient_matches(ing_name, disliked):
                hit = True
                break
        if hit:
            disliked_hits.append(r)
        else:
            clean.append(r)

    if len(clean) >= min_pool:
        return clean
    # Zu kleiner Pool → Abneigungen als Präferenz behandeln, nicht als Sperre.
    return recipes


# ─── Task 19 – Abwechslungs-Rad ────────────────────────────────────────────

async def _get_recent_recipe_ids(
    household_id: UUID,
    month: int,
    year: int,
    db: AsyncSession,
) -> set[UUID]:
    """Hole Rezept-IDs der letzten 4 Wochen (vorherige Monatspläne).

    Prüft bis zu 4 bestehende MonthlyPlans auf recipe_ids in deren MealSlots.
    """
    from sqlalchemy import select as sa_select

    stmt = (
        sa_select(MonthlyPlan)
        .where(MonthlyPlan.household_id == household_id)
        .options(selectinload(MonthlyPlan.weekly_plans).selectinload(WeeklyPlan.meal_slots))
        .order_by(MonthlyPlan.year.desc(), MonthlyPlan.month.desc())
        .limit(4)
    )
    result = await db.execute(stmt)
    existing_plans = list(result.scalars().all())

    recent: set[UUID] = set()
    for plan in existing_plans:
        # Überspringe den gleichen Monat (wird gerade generiert)
        if plan.year == year and plan.month == month:
            continue
        for wp in (plan.weekly_plans or []):
            for slot in (wp.meal_slots or []):
                recent.add(slot.recipe_id)

    return recent


def _filter_recent_recipes(
    recipes: list[Recipe],
    recent_ids: set[UUID],
) -> list[Recipe]:
    """Task 19: Entferne Rezepte, die in den letzten 4 Wochen verwendet wurden.

    Nur wenn < 20 Rezepte übrig: erlaube Wiederholung.
    """
    filtered = [r for r in recipes if r.id not in recent_ids]
    if len(filtered) >= 20:
        return filtered
    # Nicht genug Rezepte → Wiederholung erlauben
    return recipes


# ─── Task 21 – Portions-Faktor ────────────────────────────────────────────

def calculate_total_portions(members: list[dict]) -> float:
    """Task 21: Berechne Gesamt-Portionsfaktor.

    Bevorzugt einen gespeicherten Faktor aus Member.dietary_goals["portion_factor"];
    fällt sonst auf die Altersschätzung zurück:
    Alter < 4 → 0.3, 4-7 → 0.5, 8-12 → 0.7, 13+ → 1.0
    """
    total = 0.0
    for m in members:
        goals = m.get("dietary_goals") or {}
        stored = goals.get("portion_factor") if isinstance(goals, dict) else None
        if isinstance(stored, (int, float)) and not isinstance(stored, bool) and stored >= 0:
            total += float(stored)
            continue
        age = m.get("age")
        if age is None:
            total += 1.0  # Default-Erwachsener
        elif age < 4:
            total += 0.3
        elif 4 <= age <= 7:
            total += 0.5
        elif 8 <= age <= 12:
            total += 0.7
        else:
            total += 1.0
    return total


# ─── Task 20 – Balanceregel + Rezept-Auswahl ──────────────────────────────

def _pick_balanced_recipe(
    available: list[Recipe],
    used_ids: set[UUID],
    category_counter: dict[str, int],
) -> Optional[Recipe]:
    """Wählt ein Rezept unter Beachtung der Balanceregel (Task 20).

    Max 2x Nudeln, max 2x Reis, max 2x Kartoffeln, max 2x Suppe pro Woche.
    """
    for r in available:
        if r.id in used_ids:
            continue
        cat = _categorize_recipe_by_title(r.title)
        if cat and category_counter.get(cat, 0) >= MAX_PER_CATEGORY.get(cat, 2):
            continue  # Kategorie-Limit erreicht
        return r
    # Fallback: erstes verfügbares (auch wenn Limit überschritten)
    for r in available:
        if r.id not in used_ids:
            return r
    return None


# ─── Wochenplan-Generierung (mit Balance) ─────────────────────────────────

def generate_weekly_plan_skeleton(
    week_number: int,
    start_date: date,
    recipe_ids: list[UUID],
    cook_once_recipe_ids: Optional[list[UUID]] = None,
) -> dict:
    """Erzeugt ein Wochenplan-Gerüst (Slots ohne DB-Persistenz).

    Rückgabe: { "week_number": int, "start_date": date, "meal_slots": [...] }
    """
    cook_once = cook_once_recipe_ids or []
    used_recipes = set()
    slots = []

    for day in range(1, 8):  # 1=Monday .. 7=Sunday
        dinner_id = _pick_recipe(recipe_ids, used_recipes)
        used_recipes.add(dinner_id)

        slot = {
            "day_of_week": day,
            "meal_type": "dinner",
            "recipe_id": dinner_id,
            "servings_multiplier": 1.0,
            "is_repeat": False,
        }
        slots.append(slot)

        # CookOnce-EatTwice: zweite Belegung an Tag+2
        if dinner_id in cook_once:
            repeat_day = day + 2
            if repeat_day <= 7:
                slots.append({
                    "day_of_week": repeat_day,
                    "meal_type": "dinner",
                    "recipe_id": dinner_id,
                    "servings_multiplier": 1.0,
                    "is_repeat": True,
                })

    return {
        "week_number": week_number,
        "start_date": start_date,
        "meal_slots": slots,
    }


def _pick_recipe(available: list[UUID], used: set[UUID]) -> UUID:
    """Wählt ein Rezept aus (einfachster Algorithmus: erstes unbenutztes)."""
    for rid in available:
        if rid not in used:
            return rid
    return available[0]


def _week_seed(week_number: int, start_date: date) -> int:
    """Deterministischer Seed pro Woche (Monat + Jahr fließen ein)."""
    return week_number * 100003 + start_date.month * 101 + start_date.year


def _shuffle_for_week(
    available: list[Recipe],
    week_number: int,
    start_date: date,
    previous_week_ids: Optional[set[UUID]] = None,
) -> list[Recipe]:
    """Deterministisch gemischte Rezeptliste; Vorwochen-Rezepte nach hinten.

    Gleicher Monat + gleiche Config ergibt immer dieselbe Reihenfolge
    (reproduzierbarer Upsert), verschiedene Wochen unterscheiden sich.
    """
    if not available:
        return []
    rng = random.Random(_week_seed(week_number, start_date))
    # Stabile Basis-Reihenfolge: DB-Query-Reihenfolge ist nicht garantiert.
    # Nur so ist "gleicher Monat + Config => gleicher Plan" reproduzierbar.
    ordered = sorted(available, key=lambda r: str(r.id))
    shuffled = rng.sample(ordered, len(ordered))
    if previous_week_ids:
        # Sanfte Strafe: stabile Sortierung, False (nicht Vorwoche) zuerst
        shuffled.sort(key=lambda r: r.id in previous_week_ids)
    return shuffled


def _portion_multiplier(recipe: Recipe, total_portions: float) -> float:
    """Multiplier = total_portions / recipe.servings, Fallback 1.0."""
    servings = getattr(recipe, "servings", None)
    if total_portions and total_portions > 0 and servings and servings > 0:
        return total_portions / servings
    return 1.0


def _select_cook_once_for_week(
    cook_once_ids: list[UUID],
    week_number: int,
    start_date: date,
    count: int,
) -> list[UUID]:
    """Task 83: Wählt N Cook-once-Rezepte deterministisch pro Woche.

    Seed-basiert und pro Woche rotierend, damit nicht immer dieselben Rezepte
    erscheinen. Bei zu kleinem Pool werden so viele wie möglich gewählt.
    """
    if not cook_once_ids or count <= 0:
        return []
    rng = random.Random(_week_seed(week_number, start_date) + 9173)
    k = min(count, len(cook_once_ids))
    return rng.sample(list(cook_once_ids), k)


def generate_balanced_weekly_slots(
    week_number: int,
    start_date: date,
    available_recipes: list[Recipe],
    cook_once_ids: list[UUID],
    recipe_map: dict[UUID, Recipe],
    total_portions: float = 0.0,
    previous_week_ids: Optional[set[UUID]] = None,
    cook_once_enabled: bool = True,
    cook_once_count: Optional[int] = None,
) -> list[dict]:
    """Task 20/83: Erzeugt 7 Dinner-MealSlots mit Balanceregel + CookOnce.

    - Max 2x Nudeln/Reis/Kartoffeln/Suppe pro Woche (via recipe.title)
    - Task 83: N Cook-once-Rezepte werden PRO WOCHE ERZWUNGEN eingeplant
      (deterministisch, seed-basiert rotierend). Repeat-Slot an Tag+2.
    - cook_once_enabled=False: keine CookOnce-Einplanung, keine Repeat-Slots.
    - Deterministisches Shuffle pro Woche (Abwechslung zwischen Wochen)
    - servings_multiplier = total_portions / recipe.servings (Fallback 1.0)
    """
    used_ids: set[UUID] = set()
    category_counter: dict[str, int] = {}
    slots: list[dict] = []

    shuffled = _shuffle_for_week(
        available_recipes, week_number, start_date, previous_week_ids
    )

    # CookOnce deterministisch und erzwungen einplanen (Task 83).
    n = cook_once_count if cook_once_count is not None else 2
    available_ids = {r.id for r in available_recipes}
    cook_once_pool = [rid for rid in cook_once_ids if rid in available_ids]
    selected_cook_once: list[UUID] = []
    if cook_once_enabled:
        selected_cook_once = _select_cook_once_for_week(
            cook_once_pool, week_number, start_date, n
        )

    # Verteilung auf Tage: 1, 3, 5, 7 … (Repeat an Tag+2 passt in die Woche).
    forced_days: dict[int, UUID] = {}
    for idx, rid in enumerate(selected_cook_once):
        day = 1 + 2 * idx
        if day > 7:
            day = next((d for d in range(1, 8) if d not in forced_days), None)
        if day is None:
            break
        forced_days[day] = rid

    forced_recipe_ids = set(forced_days.values())

    for day in range(1, 8):  # 1=Monday .. 7=Sunday
        if day in forced_days:
            rid = forced_days[day]
            pick = next((r for r in available_recipes if r.id == rid), None)
            if pick is None:
                # Rezept nicht (mehr) verfügbar → normal weiter wählen
                pick = _pick_balanced_recipe(
                    shuffled, used_ids | forced_recipe_ids, category_counter
                )
        else:
            pick = _pick_balanced_recipe(
                shuffled, used_ids | forced_recipe_ids, category_counter
            )
        if pick is None:
            # Fallback: alle benutzt → erste Rezept wiederholen (sollte nicht passieren)
            pick = shuffled[0] if shuffled else None
            if pick is None:
                break

        used_ids.add(pick.id)
        # Category-Zähler aktualisieren
        cat = _categorize_recipe_by_title(pick.title)
        if cat:
            category_counter[cat] = category_counter.get(cat, 0) + 1

        multiplier = _portion_multiplier(pick, total_portions)

        slot = {
            "day_of_week": day,
            "meal_type": "dinner",
            "recipe_id": pick.id,
            "servings_multiplier": multiplier,
            "is_repeat": False,
        }
        slots.append(slot)

        # CookOnce-EatTwice: zweite Belegung an Tag+2 – nur wenn aktiviert.
        if cook_once_enabled and pick.id in cook_once_ids:
            repeat_day = day + 2
            if repeat_day <= 7:
                slots.append({
                    "day_of_week": repeat_day,
                    "meal_type": "dinner",
                    "recipe_id": pick.id,
                    "servings_multiplier": multiplier,
                    "is_repeat": True,
                })

    return slots


# ─── Aggregierte Generierung mit DB-Persistenz ──────────────────────────

async def _generate_and_persist_master_grocery_list(
    meal_slots: list,
    db: AsyncSession,
    household_id: UUID,
    monthly_plan_id: Optional[UUID] = None,
    supermarket: Optional[str] = None,
):
    """Variante für Master-Listen: akzeptiert eine Liste von MealSlots statt eines WeeklyPlan.

    generate_and_persist_grocery_list erwartet ein Objekt mit .meal_slots;
    für die Monats-Master-Liste reicht ein leichtgewichtiger Wrapper.
    """
    from types import SimpleNamespace
    from typing import cast

    from app.services.grocery_engine import generate_and_persist_grocery_list

    dummy_plan = cast(WeeklyPlan, SimpleNamespace(meal_slots=meal_slots))
    return await generate_and_persist_grocery_list(
        dummy_plan, db,
        household_id=household_id,
        monthly_plan_id=monthly_plan_id,
        week_number=None,
        supermarket=supermarket,
    )


async def generate_and_persist_monthly_plan(
    config: GeneratorConfig,
    db: AsyncSession,
) -> MonthlyPlan:
    """Generiert einen kompletten Monatsplan und persistiert ihn in der DB.

    Wendet nacheinander an:
      1. Task 16 – Ess-Typ-Filter (dietary_profile)
      2. Task 17 – Allergen-Prüfung (Member-Allergien)
      3. Task 19 – Abwechslungs-Rad (letzte 4 Wochen)
      4. Task 20 – Balanceregel (pro Woche max 2x Kategorie)
      5. Task 21 – Portions-Faktor (Altersgewichte → total_portions)
    """
    import calendar

    recipe_repo = RecipeRepository(db)
    recipe_map: dict[UUID, Recipe] = {}

    # Rezept-Katalog ist GLOBAL (nicht haushaltsgebunden): alle Rezepte,
    # ingredients + ingredient eager geladen. Kein Lazy-Load im Sync-Kontext
    # (sonst MissingGreenlet), kein stiller Fallback auf ungefilterte Rezepte.
    stmt = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
    )
    result = await db.execute(stmt)
    all_recipes = list(result.scalars().all())

    # Filter auf die im Config angegebenen Rezept-IDs (falls vorhanden).
    # Damit werden in Tests/Teilplänen nur die gewünschten Rezepte verwendet.
    if config.recipe_ids:
        allowed = set(config.recipe_ids)
        all_recipes = [r for r in all_recipes if r.id in allowed]

    # ── Schritt 0: Platzhalter-/Demo-Rezepte ausschließen ──
    # Muss VOR allen anderen Filtern laufen: Demo-Rezepte dürfen niemals in
    # einen Plan gelangen. Bleibt danach nichts übrig, greift weiter unten die
    # normale 400-Meldung (kein Crash, kein stiller Fallback).
    all_recipes = [r for r in all_recipes if not _is_placeholder_title(r.title)]
    recipe_map = {r.id: r for r in all_recipes}

    # ── Schritt 1: Ess-Typ-Filter (Task 16) ──
    if config.dietary_profile:
        filtered = _filter_by_diet(all_recipes, config.dietary_profile)
    else:
        filtered = all_recipes

    # Sicherheitsfilter (Diet/Allergen/Focus): NIE auf all_recipes zurückfallen.
    # Lieber ein klarer 400er als ein unpassender Plan.
    if not filtered:
        raise HTTPException(
            status_code=400,
            detail="Keine Rezepte für das gewählte Ernährungsprofil gefunden. Bitte passe das Profil an.",
        )

    # ── Schritt 2: Allergen-Prüfung (Task 17) ──
    member_allergies: list[str] = []
    for m in config.members:
        m_allergies = m.get("allergies") or []
        if isinstance(m_allergies, str):
            m_allergies = [m_allergies]
        elif not isinstance(m_allergies, (list, tuple)):
            m_allergies = []
        member_allergies.extend(m_allergies)
    # Haushalts-Allergien aus dem Profil ebenfalls berücksichtigen (Frontend-Format).
    profile_allergies = (config.dietary_profile or {}).get("allergies") or []
    if isinstance(profile_allergies, str):
        profile_allergies = [profile_allergies]
    elif not isinstance(profile_allergies, (list, tuple)):
        profile_allergies = []
    member_allergies.extend(profile_allergies)
    # Deduplizieren
    member_allergies = list(set(a.strip().lower() for a in member_allergies if a))

    if member_allergies:
        ing_id_to_name, recipe_ing_ids, ing_id_to_cat = _build_ingredient_index(filtered)
        filtered = _filter_by_allergens(
            filtered, member_allergies,
            ing_id_to_name, ing_id_to_cat, recipe_ing_ids,
        )
        if not filtered:
            raise HTTPException(
                status_code=400,
                detail=f"Keine Rezepte für die Allergene {member_allergies} gefunden. Bitte passe die Allergien an.",
            )

    # ── Schritt 2a2: Abneigungen (Task 35) – weiche Regel ──
    # Geschmackliche Ablehnung darf den Plan nicht blockieren: Rezepte mit
    # Abneigung fliegen nur raus, wenn danach noch genug Auswahl bleibt.
    disliked = _parse_dislikes(config.dietary_profile or {})
    if disliked:
        ing_id_to_name_d, recipe_ing_ids_d, _ = _build_ingredient_index(filtered)
        filtered = _filter_by_dislikes(
            filtered, disliked, ing_id_to_name_d, recipe_ing_ids_d,
        )

    # ── Schritt 2b: Fokus-Tags (Task 51) ──
    if config.focus_tags:
        focus_set = {t.lower().strip() for t in config.focus_tags if t}
        filtered = [
            r for r in filtered
            if focus_set & {t.lower().strip() for t in (r.tags or [])}
        ]
        if not filtered:
            raise HTTPException(
                status_code=400,
                detail=f"Keine Rezepte für die Fokustags {config.focus_tags} gefunden. Bitte passe die Fokustags an.",
            )

    # ── Schritt 2c: Saison-Filter (Monat) ──
    # Muss NACH Fokus-Tags und VOR dem Abwechslungs-Rad laufen. Kein stiller Fallback:
    # bei 0 Treffern klarer 400er statt unpassender Rezepte.
    filtered = _filter_by_season(filtered, config.month)
    if not filtered:
        raise HTTPException(
            status_code=400,
            detail=(
                "Keine saisonal passenden Rezepte fuer den gewaehlten Monat gefunden"
            ),
        )

    # ── Schritt 3: Abwechslungs-Rad (Task 19) ──
    # Nur der Abwechslungs-Filter darf auf den safety-gefilterten Pool zurückfallen,
    # niemals auf all_recipes (sonst wieder stiller Fallback auf unpassende Rezepte).
    safety_pool = filtered
    recent_ids = await _get_recent_recipe_ids(
        config.household_id, config.month, config.year, db
    )
    if recent_ids:
        filtered = _filter_recent_recipes(filtered, recent_ids)
        if len(filtered) < 5:
            filtered = safety_pool

    # ── Schritt 4: Monatsplan anlegen ──
    num_weeks = weeks_in_month(config.month, config.year)
    first_day = date(config.year, config.month, 1)

    # Stabile Reihenfolge auch fuer die CookOnce-Auswahl (Reproduzierbarkeit).
    filtered = sorted(filtered, key=lambda r: str(r.id))

    # Task 83: CookOnce-Einstellungen aus Profil/Config lesen. cook_once_ids
    # kommen aus dem saisonal/diet-gefilterten Pool (NICHT aus all_recipes)
    # und werden NICHT hier auf N gekürzt – die Wochenauswahl rotiert
    # deterministisch in generate_balanced_weekly_slots.
    profile = config.dietary_profile or {}
    cook_once_enabled = bool(profile.get("cook_once_enabled", config.cook_once_enabled))
    cook_once_count = profile.get("cook_once_count", config.cook_once_count)
    try:
        cook_once_count = int(cook_once_count)
    except (TypeError, ValueError):
        cook_once_count = 2
    cook_once_ids = [
        r.id for r in filtered
        if r.cook_once_eat_twice
    ]

    # ── Upsert: existierenden Plan für (household, month, year) wiederverwenden ──
    # Keine Duplikate: zugehörige WeeklyPlans/MealSlots/GroceryLists werden
    # gelöscht und neu erzeugt; der MonthlyPlan selbst behält seine plan_id.
    import datetime as _dt

    plan_repo = MonthlyPlanRepository(db)
    existing_plans = (
        await db.execute(
            select(MonthlyPlan)
            .where(
                MonthlyPlan.household_id == config.household_id,
                MonthlyPlan.month == config.month,
                MonthlyPlan.year == config.year,
            )
            .order_by(MonthlyPlan.generated_at.asc().nulls_first(), MonthlyPlan.id.asc())
        )
    ).scalars().all()

    created = not existing_plans
    if existing_plans:
        monthly = existing_plans[0]
        plan_ids = [p.id for p in existing_plans]
        # Abhängige Daten explizit löschen (bulk delete, kein ORM-Lazy-Load).
        await db.execute(
            delete(GroceryItem).where(
                GroceryItem.grocery_list_id.in_(
                    select(GroceryList.id).where(GroceryList.monthly_plan_id.in_(plan_ids))
                )
            )
        )
        await db.execute(
            delete(GroceryList).where(GroceryList.monthly_plan_id.in_(plan_ids))
        )
        await db.execute(
            delete(MealSlot).where(
                MealSlot.weekly_plan_id.in_(
                    select(WeeklyPlan.id).where(WeeklyPlan.monthly_plan_id.in_(plan_ids))
                )
            )
        )
        await db.execute(
            delete(WeeklyPlan).where(WeeklyPlan.monthly_plan_id.in_(plan_ids))
        )
        # Bereits vorhandene Duplikate (Altbestand) mit entfernen.
        duplicate_ids = plan_ids[1:]
        if duplicate_ids:
            await db.execute(delete(MonthlyPlan).where(MonthlyPlan.id.in_(duplicate_ids)))
        monthly.status = "draft"
        monthly.focus_tags = config.focus_tags or []
        monthly.generated_at = _dt.datetime.now(_dt.UTC)
        monthly.total_portions = config.total_portions
        await db.flush()
    else:
        monthly = await plan_repo.create(
            household_id=config.household_id,
            month=config.month,
            year=config.year,
            status="draft",
            focus_tags=config.focus_tags or [],
            generated_at=_dt.datetime.now(_dt.UTC),
            total_portions=config.total_portions,
        )

    # WeeklyPlans + MealSlots generieren
    week_repo = WeeklyPlanRepository(db)
    slot_repo = MealSlotRepository(db)

    from app.services.grocery_engine import generate_and_persist_grocery_list

    previous_week_ids: set[UUID] = set()
    profile = config.dietary_profile or {}
    shopping_frequency = profile.get("shopping_frequency")
    shopping_days = profile.get("shopping_days") or []
    supermarket = profile.get("preferred_supermarket")
    # "nach_bedarf" oder keine Angabe: EINE Master-Liste für den gesamten Monat.
    # Alle anderen Frequenzen (1x_woche, 2x_woche, mehrmals_woche): pro Woche eine Liste.
    is_master_list = shopping_frequency in (None, "", "nach_bedarf")
    all_slots_for_master: list = []

    for week_idx in range(num_weeks):
        week_start = first_day + timedelta(weeks=week_idx)
        week_num = week_idx + 1

        weekly = await week_repo.create(
            household_id=config.household_id,
            monthly_plan_id=monthly.id,
            week_number=week_num,
            start_date=week_start,
        )

        # Task 20/83: Balancede Slots mit Kategorie-Regeln, Abwechslungs-Shuffle
        # und erzwungener CookOnce-Einplanung.
        slot_dicts = generate_balanced_weekly_slots(
            week_number=week_num,
            start_date=week_start,
            available_recipes=filtered,
            cook_once_ids=cook_once_ids,
            recipe_map=recipe_map,
            total_portions=config.total_portions,
            previous_week_ids=previous_week_ids,
            cook_once_enabled=cook_once_enabled,
            cook_once_count=cook_once_count,
        )

        for sd in slot_dicts:
            slot = await slot_repo.create(
                weekly_plan_id=weekly.id,
                day_of_week=sd["day_of_week"],
                meal_type=sd["meal_type"],
                recipe_id=sd["recipe_id"],
                servings_multiplier=sd["servings_multiplier"],
                is_repeat=sd["is_repeat"],
            )
            all_slots_for_master.append(slot)

        if not is_master_list:
            # Einkaufsliste je Woche mit echter ISO-Kalenderwoche erzeugen.
            # Task 85: Bei gesetzten shopping_days wird die Woche in Segmente
            # geteilt (ein Einkaufstag startet ein neues Segment).
            await db.flush()
            weekly_with_slots = (
                await db.execute(
                    select(WeeklyPlan)
                    .where(WeeklyPlan.id == weekly.id)
                    .options(selectinload(WeeklyPlan.meal_slots))
                )
            ).scalars().first()
            if weekly_with_slots is not None:
                from types import SimpleNamespace
                from typing import cast as _cast
                segments = _segment_slots_by_shopping_days(
                    weekly_with_slots.meal_slots, shopping_days
                )
                for segment_label, seg_slots in segments:
                    dummy_plan = _cast(WeeklyPlan, SimpleNamespace(meal_slots=seg_slots))
                    await generate_and_persist_grocery_list(
                        dummy_plan, db,
                        household_id=config.household_id,
                        monthly_plan_id=monthly.id,
                        week_number=week_start.isocalendar()[1],
                        supermarket=supermarket,
                        segment_label=segment_label,
                    )

        previous_week_ids = {sd["recipe_id"] for sd in slot_dicts}

    if is_master_list:
        # Master-Liste: alle Slots des Monats in einer Einkaufsliste zusammenfassen.
        await db.flush()
        await _generate_and_persist_master_grocery_list(
            all_slots_for_master, db,
            household_id=config.household_id,
            monthly_plan_id=monthly.id,
            supermarket=supermarket,
        )

    await db.refresh(monthly)
    # Flag für die API-Response (created=false / updated=true bei Upsert)
    monthly.was_created = created
    return monthly


# ─── Legacy: In-Memory-Generierung (für bestehende Tests) ────────────────

def generate_monthly_plan(config: GeneratorConfig) -> dict:
    """Generiert einen kompletten Monatsplan als Dict-Struktur (In-Memory).

    Legacy-Funktion für bestehende Tests. Nutzt keine DB.
    """
    import calendar
    num_weeks = weeks_in_month(config.month, config.year)
    first_day = date(config.year, config.month, 1)

    weeks = []
    for week_idx in range(num_weeks):
        week_start = first_day + timedelta(weeks=week_idx)
        week_num = week_idx + 1

        cook_once = config.recipe_ids[:config.cook_once_eat_twice_count] if config.cook_once_eat_twice_count > 0 else []

        slot_dicts = generate_weekly_plan_skeleton(
            week_number=week_num,
            start_date=week_start,
            recipe_ids=config.recipe_ids,
            cook_once_recipe_ids=cook_once,
        )["meal_slots"]

        weeks.append({
            "week_number": week_num,
            "start_date": week_start,
            "meal_slots": slot_dicts,
        })

    return {
        "month": config.month,
        "year": config.year,
        "weeks": weeks,
    }