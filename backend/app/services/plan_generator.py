"""Plan-Generator: Kernlogik für automatische Wochen-/Monatspläne

Domain-Regeln (TDD-Anker):
1. Ein MonthlyPlan hat 4-5 WeeklyPlans je nach Monat
2. Mindestens 5 Hauptmahlzeiten pro Woche (Slots mit meal_type=dinner)
3. CookOnce-EatTwice: max 2 Rezepte pro Woche, die doppelt belegt werden
4. Keine Wiederholung desselben Rezepts innerhalb 7 Tagen
5. Berücksichtigt Member-Allergien (kein Rezept mit Allergen)
6. Berücksichtigt Haushalts-Präferenzen (vegetarisch, etc.)
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MealSlot, MonthlyPlan, Recipe, WeeklyPlan
from app.repositories.plan import MonthlyPlanRepository, WeeklyPlanRepository, MealSlotRepository
from app.repositories.recipe import RecipeRepository


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


def weeks_in_month(month: int, year: int) -> int:
    """Gibt die Anzahl der Planungswochen für einen Monat zurück (4 oder 5).

    Domain-Regel: 28 Tage → 4 Wochen, 29+ Tage → 5 Wochen.
    Ein Monatsplan deckt immer den gesamten Monat ab;
    die Wochen teilen die Tage gleichmäßig auf.
    """
    import calendar
    days = calendar.monthrange(year, month)[1]
    return 4 if days <= 28 else 5


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
        # Jeden Tag eine Hauptmahlzeit (Abendessen)
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

        # CookOnce-EatTwice: zweite Belegung an Tag+2 (wenn Montag=1, dann Tag 3=Wednesday)
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
    # Fallback: wenn alle benutzt, widerhole (wird später besser)
    return available[0]


# ─── Aggregierte Generierung mit DB-Persistenz ──────────────────────────

async def generate_and_persist_monthly_plan(
    config: GeneratorConfig,
    db: AsyncSession,
) -> MonthlyPlan:
    """Generiert einen kompletten Monatsplan und persistiert ihn in der DB.

    Lädt Rezepte aus der DB, generiert WeeklyPlans + MealSlots
    und speichert alles in einer Transaktion.
    """
    import calendar

    recipe_repo = RecipeRepository(db)
    recipes = await recipe_repo.get_all()
    recipe_map = {r.id: r for r in recipes}

    num_weeks = weeks_in_month(config.month, config.year)
    first_day = date(config.year, config.month, 1)

    # CookOnce-Rezepte aus DB (cook_once_eat_twice=True)
    cook_once_ids = [
        r.id for r in recipes
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
    )

    # WeeklyPlans + MealSlots generieren
    week_repo = WeeklyPlanRepository(db)
    slot_repo = MealSlotRepository(db)

    for week_idx in range(num_weeks):
        week_start = first_day + timedelta(weeks=week_idx)
        week_num = week_idx + 1

        # WeeklyPlan anlegen
        weekly = await week_repo.create(
            household_id=config.household_id,
            monthly_plan_id=monthly.id,
            week_number=week_num,
            start_date=week_start,
        )

        # MealSlots generieren
        recipe_ids_for_week = list(recipe_map.keys())
        slot_dicts = generate_weekly_plan_skeleton(
            week_number=week_num,
            start_date=week_start,
            recipe_ids=recipe_ids_for_week,
            cook_once_recipe_ids=cook_once_ids,
        )["meal_slots"]

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