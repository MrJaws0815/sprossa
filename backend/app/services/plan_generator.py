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
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    MealSlot, MonthlyPlan, Recipe, WeeklyPlan, RecipeIngredient, Ingredient,
)
from app.repositories.plan import MonthlyPlanRepository, WeeklyPlanRepository, MealSlotRepository
from app.repositories.recipe import RecipeRepository


# ─── Allergen-Mapping-Tabelle (Task 17) ────────────────────────────────────

ALLERGEN_MAP: dict[str, list[str]] = {
    "gluten": ["Weizenmehl", "Mehl", "Nudeln", "Brot", "Haferflocken", "Dinkel", "Grieß"],
    "laktose": ["Milch", "Sahne", "Joghurt", "Butter", "Käse", "Frischkäse", "Quark", "Kefir"],
    "nuesse": ["Mandeln", "Walnüsse", "Haselnüsse", "Cashewkerne", "Erdnüsse", "Pistazien", "Pinienkerne"],
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


# ─── Task 16 – Ess-Typ-Filter ──────────────────────────────────────────────

def _categorize_recipe_by_title(title: str) -> Optional[str]:
    """Bestimmt die Kategorie eines Rezepts anhand des Titels (Task 20)."""
    title_lower = title.lower()
    for category, keywords in RECIPE_CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in title_lower:
                return category
    return None


def _filter_by_diet(recipes: list[Recipe], dietary_profile: dict) -> list[Recipe]:
    """Task 16: Filtere Rezepte basierend auf der Ernährungsweise des Haushalts.

    dietary_profile = {"type": "vegetarisch"|"vegan"|"veggie"|"vollkost"}
    Tags in recipes: fleisch, fisch, vegetarisch, vegan, veggie
    """
    profile = (dietary_profile or {}).get("type", "").lower().strip()
    if not profile or profile in ("vollkost", "mix", ""):
        return recipes

    filtered: list[Recipe] = []
    for r in recipes:
        tags = [t.lower().strip() for t in (r.tags or [])]
        if profile in ("vegetarisch", "veggie"):
            # Vegetarisch: kein Fleisch, kein Fisch
            if "fleisch" in tags or "fisch" in tags:
                continue
        elif profile == "vegan":
            # Vegan: zusätzlich keine Milch, keine Eier
            if "fleisch" in tags or "fisch" in tags or "milch" in tags or "eier" in tags:
                continue
        # Bei unbekanntem Profil: alle durchlassen
        filtered.append(r)
    return filtered


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


def _build_allergen_set(member_allergies: list[str]) -> set[str]:
    """Baut ein Set von ingrendient_names (lowercase), die Allergene triggern."""
    if not member_allergies:
        return set()
    allergen_set: set[str] = set()
    for allergy in member_allergies:
        allergy_lower = allergy.lower().strip()
        if allergy_lower in ALLERGEN_MAP:
            for name in ALLERGEN_MAP[allergy_lower]:
                allergen_set.add(name.lower())
    return allergen_set


def _build_allergen_categories(member_allergies: list[str]) -> set[str]:
    """Baut ein Set von ingredient.category-Werten, die Allergene triggern."""
    category_map: dict[str, set[str]] = {
        "laktose": {"dairy"},
        "fleisch": {"meat"},
        "fisch": {"fish", "meat"},
        "nuesse": {"nuts", "spices"},
    }
    cats: set[str] = set()
    for allergy in member_allergies:
        allergy_lower = allergy.lower().strip()
        if allergy_lower in category_map:
            cats.update(category_map[allergy_lower])
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
    allergen_cats = _build_allergen_categories(member_allergies)

    filtered: list[Recipe] = []
    for r in recipes:
        has_allergen = False
        for ing_id in recipe_ing_ids.get(r.id, []):
            ing_name = ing_id_to_name.get(ing_id, "").lower()
            ing_cat = ing_id_to_cat.get(ing_id, "").lower()
            if ing_name in allergen_names:
                has_allergen = True
                break
            if ing_cat in allergen_cats:
                has_allergen = True
                break
        if not has_allergen:
            filtered.append(r)
    return filtered


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
    """Task 21: Berechne Gesamt-Portionsfaktor basierend auf Alter.

    Alter < 4 → 0.3, 4-7 → 0.5, 8-12 → 0.7, 13+ → 1.0
    """
    total = 0.0
    for m in members:
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


def generate_balanced_weekly_slots(
    week_number: int,
    start_date: date,
    available_recipes: list[Recipe],
    cook_once_ids: list[UUID],
    recipe_map: dict[UUID, Recipe],
) -> list[dict]:
    """Task 20: Erzeugt 7 Dinner-MealSlots mit Balanceregel + CookOnce.

    - Max 2x Nudeln/Reis/Kartoffeln/Suppe pro Woche (via recipe.title)
    - CookOnce-EatTwice: Repeat an Tag+2
    """
    used_ids: set[UUID] = set()
    category_counter: dict[str, int] = {}
    slots: list[dict] = []

    for day in range(1, 8):  # 1=Monday .. 7=Sunday
        pick = _pick_balanced_recipe(available_recipes, used_ids, category_counter)
        if pick is None:
            # Fallback: alle benutzt → erste Rezept wiederholen (sollte nicht passieren)
            pick = available_recipes[0] if available_recipes else None
            if pick is None:
                break

        used_ids.add(pick.id)
        # Category-Zähler aktualisieren
        cat = _categorize_recipe_by_title(pick.title)
        if cat:
            category_counter[cat] = category_counter.get(cat, 0) + 1

        slot = {
            "day_of_week": day,
            "meal_type": "dinner",
            "recipe_id": pick.id,
            "servings_multiplier": 1.0,
            "is_repeat": False,
        }
        slots.append(slot)

        # CookOnce-EatTwice: zweite Belegung an Tag+2
        if pick.id in cook_once_ids:
            repeat_day = day + 2
            if repeat_day <= 7:
                slots.append({
                    "day_of_week": repeat_day,
                    "meal_type": "dinner",
                    "recipe_id": pick.id,
                    "servings_multiplier": 1.0,
                    "is_repeat": True,
                })

    return slots


# ─── Aggregierte Generierung mit DB-Persistenz ──────────────────────────

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

    # Rezepte MIT ingredients eager laden
    stmt = (
        select(Recipe)
        .where(Recipe.household_id == config.household_id)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
    )
    result = await db.execute(stmt)
    all_recipes = list(result.scalars().all())
    recipe_map = {r.id: r for r in all_recipes}

    if not all_recipes:
        # Fallback auf recipe_repo.get_all()
        all_recipes = await recipe_repo.get_all()
        recipe_map = {r.id: r for r in all_recipes}

    # ── Schritt 1: Ess-Typ-Filter (Task 16) ──
    if config.dietary_profile:
        filtered = _filter_by_diet(all_recipes, config.dietary_profile)
    else:
        filtered = all_recipes

    # ── Schritt 2: Allergen-Prüfung (Task 17) ──
    member_allergies: list[str] = []
    for m in config.members:
        member_allergies.extend(m.get("allergies") or [])
    # Deduplizieren
    member_allergies = list(set(a.strip().lower() for a in member_allergies if a))

    if member_allergies:
        ing_id_to_name, recipe_ing_ids, ing_id_to_cat = _build_ingredient_index(filtered)
        filtered = _filter_by_allergens(
            filtered, member_allergies,
            ing_id_to_name, ing_id_to_cat, recipe_ing_ids,
        )

    # ── Schritt 3: Abwechslungs-Rad (Task 19) ──
    recent_ids = await _get_recent_recipe_ids(
        config.household_id, config.month, config.year, db
    )
    if recent_ids:
        filtered = _filter_recent_recipes(filtered, recent_ids)

    # Fallback: falls zu wenige Rezepte übrig
    if len(filtered) < 5:
        # Mindestens 5 verschiedene Rezepte für Abwechslung
        filtered = all_recipes

    # ── Schritt 4: Monatsplan anlegen ──
    num_weeks = weeks_in_month(config.month, config.year)
    first_day = date(config.year, config.month, 1)

    # CookOnce-Rezepte aus den gefilterten Rezepten
    cook_once_ids = [
        r.id for r in filtered
        if r.cook_once_eat_twice
    ][:config.cook_once_eat_twice_count]

    # MonthlyPlan anlegen
    plan_repo = MonthlyPlanRepository(db)
    monthly = await plan_repo.create(
        household_id=config.household_id,
        month=config.month,
        year=config.year,
        status="draft",
        focus_tags=config.focus_tags or [],
        generated_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        total_portions=config.total_portions,
    )

    # WeeklyPlans + MealSlots generieren
    week_repo = WeeklyPlanRepository(db)
    slot_repo = MealSlotRepository(db)

    for week_idx in range(num_weeks):
        week_start = first_day + timedelta(weeks=week_idx)
        week_num = week_idx + 1

        weekly = await week_repo.create(
            household_id=config.household_id,
            monthly_plan_id=monthly.id,
            week_number=week_num,
            start_date=week_start,
        )

        # Task 20: Balancede Slots mit Kategorie-Regeln
        slot_dicts = generate_balanced_weekly_slots(
            week_number=week_num,
            start_date=week_start,
            available_recipes=filtered,
            cook_once_ids=cook_once_ids,
            recipe_map=recipe_map,
        )

        for sd in slot_dicts:
            await slot_repo.create(
                weekly_plan_id=weekly.id,
                day_of_week=sd["day_of_week"],
                meal_type=sd["meal_type"],
                recipe_id=sd["recipe_id"],
                servings_multiplier=sd["servings_multiplier"],
                is_repeat=sd["is_repeat"],
            )

    await db.refresh(monthly)
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